const express = require('express');
const path = require('path');
const helmet = require('helmet');
const compression = require('compression');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// JSON body parser for license API
app.use(express.json());

// Security and performance middleware
app.use(helmet({
  contentSecurityPolicy: false // Allows CDN fonts, Tailwind, and FontAwesome
}));
app.use(compression());

// Persistent database paths
const DATA_DIR = path.join(__dirname, 'data');
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

const TRIALS_DB_PATH = path.join(DATA_DIR, 'trials.json');
const LICENSES_DB_PATH = path.join(DATA_DIR, 'licenses.json');

function loadJsonDb(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    }
  } catch (e) {
    console.error(`Error reading ${filePath}:`, e);
  }
  return {};
}

function saveJsonDb(filePath, data) {
  try {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
  } catch (e) {
    console.error(`Error saving ${filePath}:`, e);
  }
}

// Serve static directory assets
app.use(express.static(path.join(__dirname)));

// --- HARDWARE-LOCKED LICENSING & ₹99 TEST FLIGHT API ---

// Helper to compute remaining test flight days
function computeTestFlightStatus(lic, machine_id) {
  const activatedTime = new Date(lic.activated_at || lic.created_at).getTime();
  const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;
  const expiresAt = activatedTime + SEVEN_DAYS_MS;
  const remainingMs = expiresAt - Date.now();

  if (remainingMs > 0) {
    const daysRemaining = Math.ceil(remainingMs / (24 * 60 * 60 * 1000));
    return {
      status: 'licensed',
      tier: 'test_flight',
      days_remaining: daysRemaining,
      trial_expires: new Date(expiresAt).toISOString(),
      machine_id,
      message: `Nia 7-Day Test Flight Active (${daysRemaining} day(s) remaining).`
    };
  } else {
    return {
      status: 'trial_expired',
      tier: 'test_flight',
      days_remaining: 0,
      trial_expires: new Date(expiresAt).toISOString(),
      machine_id,
      message: 'Your 7-day ₹99 Test Flight has expired. Upgrade to Nia Pro or Lifetime BYOK to continue.'
    };
  }
}

// 1. Check Trial & License Status
app.post('/api/license/check-trial', (req, res) => {
  const { machine_id, license_key } = req.body || {};

  if (!machine_id) {
    return res.status(400).json({ error: 'machine_id is required' });
  }

  const licenses = loadJsonDb(LICENSES_DB_PATH);

  // Case A: A license key is provided in the request
  if (license_key) {
    const cleanKey = license_key.trim().toUpperCase();
    if (!licenses[cleanKey]) {
      return res.status(404).json({
        status: 'invalid_key',
        message: 'Invalid license key. Please verify your purchase receipt or get a key at ndtechhub.com'
      });
    }

    const lic = licenses[cleanKey];

    // Bind machine_id on first activation
    if (!lic.bound_machine_id) {
      lic.bound_machine_id = machine_id;
      lic.activated_at = new Date().toISOString();
      saveJsonDb(LICENSES_DB_PATH, licenses);
    }

    if (lic.bound_machine_id !== machine_id) {
      return res.status(403).json({
        status: 'license_bound_error',
        message: 'License key is already registered to a different computer.'
      });
    }

    // If Test Flight key, evaluate 7-day window
    if (lic.tier === 'test_flight') {
      return res.json(computeTestFlightStatus(lic, machine_id));
    }

    return res.json({
      status: 'licensed',
      tier: lic.tier || 'pro',
      message: `Nia ${lic.tier ? lic.tier.toUpperCase() : 'PRO'} License Active`,
      machine_id
    });
  }

  // Case B: No key provided — check if this hardware ID is already bound to a valid license
  const boundKey = Object.keys(licenses).find(k => licenses[k].bound_machine_id === machine_id);
  if (boundKey) {
    const lic = licenses[boundKey];
    if (lic.tier === 'test_flight') {
      return res.json(computeTestFlightStatus(lic, machine_id));
    }
    return res.json({
      status: 'licensed',
      tier: lic.tier || 'pro',
      message: `Nia ${lic.tier ? lic.tier.toUpperCase() : 'PRO'} License Active`,
      machine_id
    });
  }

  // Unlicensed hardware without key
  return res.json({
    status: 'key_required',
    days_remaining: 0,
    machine_id,
    message: 'License key required. Please purchase a ₹99 Test Flight or Pro license at ndtechhub.com'
  });
});

// 2. Activate License Key
app.post('/api/license/activate', (req, res) => {
  const { machine_id, license_key } = req.body || {};

  if (!machine_id || !license_key) {
    return res.status(400).json({ error: 'machine_id and license_key are required' });
  }

  const cleanKey = license_key.trim().toUpperCase();
  const licenses = loadJsonDb(LICENSES_DB_PATH);

  if (!licenses[cleanKey]) {
    return res.status(404).json({
      status: 'invalid_key',
      message: 'Invalid license key. Please check the key received upon purchase.'
    });
  }

  const lic = licenses[cleanKey];
  if (lic.bound_machine_id && lic.bound_machine_id !== machine_id) {
    return res.status(403).json({
      status: 'already_activated',
      message: 'This license key is already bound to another machine.'
    });
  }

  lic.bound_machine_id = machine_id;
  lic.activated_at = lic.activated_at || new Date().toISOString();
  saveJsonDb(LICENSES_DB_PATH, licenses);

  if (lic.tier === 'test_flight') {
    return res.json({
      status: 'success',
      tier: 'test_flight',
      message: 'Nia 7-Day Test Flight successfully activated! Enjoy 7 days of full Pro access.'
    });
  }

  res.json({
    status: 'success',
    tier: lic.tier || 'pro',
    message: 'Nia License successfully activated!'
  });
});

// 3. Admin / Webhook key generator (e.g. called after Razorpay / Stripe payment)
app.post('/api/license/generate', (req, res) => {
  const { secret, customer_email, tier = 'pro' } = req.body || {};
  const ADMIN_SECRET = process.env.ADMIN_SECRET || 'ndtechhub_admin_secret_2026';

  if (secret !== ADMIN_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const randomSegment = () => Math.random().toString(36).substring(2, 6).toUpperCase();
  const newKey = `NIA-${randomSegment()}-${randomSegment()}-${randomSegment()}`;

  const licenses = loadJsonDb(LICENSES_DB_PATH);
  licenses[newKey] = {
    created_at: new Date().toISOString(),
    customer_email: customer_email || 'anonymous',
    tier: tier,
    bound_machine_id: null,
    status: 'active'
  };
  saveJsonDb(LICENSES_DB_PATH, licenses);

  res.json({
    success: true,
    license_key: newKey,
    tier,
    customer_email
  });
});

const GITHUB_RELEASE_DOWNLOAD_URL = 'https://github.com/manojalig2979-dot/nia0.1/releases/download/v1.0.0/Nia-Setup-1.0.exe';

// API endpoint to check release status
app.get('/api/status', (req, res) => {
  const filePath = path.join(__dirname, 'downloads', 'Nia-Setup-1.0.exe');
  const agentExePath = path.join(__dirname, '..', 'nia_agent', 'dist', 'NiaAgent.exe');
  
  let installerFound = true;
  let fileSizeMb = "510.8";

  if (fs.existsSync(filePath)) {
    fileSizeMb = (fs.statSync(filePath).size / (1024 * 1024)).toFixed(1);
  } else if (fs.existsSync(agentExePath)) {
    fileSizeMb = (fs.statSync(agentExePath).size / (1024 * 1024)).toFixed(1);
  }

  res.json({
    name: 'Nia 1.0',
    version: '1.0.0 Stable',
    platform: 'Windows 10/11 (64-bit)',
    installerAvailable: installerFound,
    installerSizeMb: fileSizeMb,
    releaseDownloadUrl: GITHUB_RELEASE_DOWNLOAD_URL,
    commercial_tiers: {
      test_flight: { price_inr: 99, price_usd: 1, duration_days: 7, auto_converts_to: "pro" },
      starter: { price_inr: 899, price_usd: 12, billing: "monthly", smart_tasks: 500 },
      pro: { price_inr: 1799, price_usd: 24, billing: "monthly", smart_tasks: "unlimited" },
      lifetime_byok: { price_inr: 6999, price_usd: 99, billing: "one_time", server_cost: 0 }
    },
    voiceEngine: 'Microsoft Swara Neural (Hinglish/Hindi/English)',
    architecture: 'Local DAG Supervisor',
    author: 'NDTechHub'
  });
});

// Single-click binary download endpoint
app.get('/download/installer', (req, res) => {
  const primaryPath = path.join(__dirname, 'downloads', 'Nia-Setup-1.0.exe');
  
  if (fs.existsSync(primaryPath)) {
    const stat = fs.statSync(primaryPath);
    res.setHeader('Content-Disposition', 'attachment; filename="Nia-Setup-1.0.exe"');
    res.setHeader('Content-Type', 'application/vnd.microsoft.portable-executable');
    res.setHeader('Content-Length', stat.size);
    const fileStream = fs.createReadStream(primaryPath);
    return fileStream.pipe(res);
  }

  // Fallback to high-speed CDN download from official GitHub Release
  return res.redirect(302, GITHUB_RELEASE_DOWNLOAD_URL);
});

// Single Page Application fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`[NDTechHub] Nia 1.0 distribution & licensing server online at http://localhost:${PORT}`);
});