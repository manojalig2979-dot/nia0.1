const express = require('express');
const path = require('path');
const helmet = require('helmet');
const compression = require('compression');
const fs = require('fs');
const nodemailer = require('nodemailer');
const { v4: uuidv4 } = require('uuid');

// Configure NodeMailer transporter (Dummy configuration for local testing, replace with real credentials in production)
const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST || 'smtp.mailtrap.io',
    port: process.env.SMTP_PORT || 2525,
    auth: {
        user: process.env.SMTP_USER || 'your_username',
        pass: process.env.SMTP_PASS || 'your_password'
    }
});
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
  const ADMIN_SECRET = process.env.ADMIN_SECRET || 'Msrknsds@0304';
  const DEMO_SECRET = 'ndtechhub_checkout_demo_2026';

  if (secret !== ADMIN_SECRET && secret !== DEMO_SECRET) {
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

// 4. Payment Gateway Webhook (Razorpay/Stripe)
app.post('/api/payment-webhook', async (req, res) => {
  // In production, verify the webhook signature from Stripe/Razorpay here
  const { payment_status, customer_email, tier = 'pro' } = req.body || {};

  if (payment_status !== 'success' || !customer_email) {
    return res.status(400).json({ error: 'Invalid payload or payment not successful' });
  }

  // Generate License
  const randomSegment = () => Math.random().toString(36).substring(2, 6).toUpperCase();
  const newKey = `NIA-${randomSegment()}-${randomSegment()}-${randomSegment()}`;

  const licenses = loadJsonDb(LICENSES_DB_PATH);
  licenses[newKey] = {
    created_at: new Date().toISOString(),
    customer_email: customer_email,
    tier: tier,
    bound_machine_id: null,
    status: 'active',
    payment_id: req.body.payment_id || uuidv4() // Use passed payment ID or generate one
  };
  saveJsonDb(LICENSES_DB_PATH, licenses);

  // Send Email
  const mailOptions = {
    from: '"NIA Support" <support@ndtechhub.com>',
    to: customer_email,
    subject: `Your NIA ${tier.toUpperCase()} License Key`,
    html: `
      <h2>Thank you for your purchase!</h2>
      <p>Your NIA Desktop Agent is ready to use.</p>
      <div style="padding: 15px; background-color: #f4f4f4; border-radius: 5px; font-size: 18px; margin: 20px 0;">
        <strong>Your License Key:</strong> <span style="color: #3d8ef8;">${newKey}</span>
      </div>
      <p><strong>How to activate:</strong></p>
      <ol>
        <li>Open the NIA Desktop Application.</li>
        <li>Go to <strong>Settings</strong> > <strong>System & AI Settings</strong>.</li>
        <li>Paste your License Key into the input field and click Save.</li>
      </ol>
      <p>If you haven't downloaded the app yet, <a href="https://ndtechhub.com/downloads">download it here</a>.</p>
    `
  };

  try {
    await transporter.sendMail(mailOptions);
    console.log(`License key emailed successfully to ${customer_email}`);
  } catch (err) {
    console.error('Failed to send email:', err);
    // Continue anyway so we return 200 OK to the payment gateway
  }

  res.status(200).json({ received: true, license_key: newKey });
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

// Contact Us Form Submission API
const CONTACTS_DB_PATH = path.join(DATA_DIR, 'contacts.json');
app.post('/api/contact', (req, res) => {
  const { name, email, inquiry_type, subject, message } = req.body || {};
  if (!name || !email || !message) {
    return res.status(400).json({ error: 'Name, email, and message are required.' });
  }

  const contacts = loadJsonDb(CONTACTS_DB_PATH);
  const contactId = 'CNT-' + Date.now();
  contacts[contactId] = {
    id: contactId,
    name,
    email,
    inquiry_type: inquiry_type || 'general',
    subject: subject || 'No Subject',
    message,
    created_at: new Date().toISOString()
  };
  saveJsonDb(CONTACTS_DB_PATH, contacts);

  console.log(`[NDTechHub] Received contact inquiry from ${name} (${email}) - Type: ${inquiry_type}`);

  // Optional instant webhook notification (e.g. Discord, Telegram, Slack, or Make/Zapier)
  const webhookUrl = process.env.NOTIFICATION_WEBHOOK_URL || process.env.CONTACT_WEBHOOK_URL;
  if (webhookUrl) {
    try {
      fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: `📬 **New Contact Inquiry on Nia 1.0**\n**From:** ${name} (${email})\n**Category:** ${inquiry_type}\n**Subject:** ${subject}\n**Message:**\n${message}`
        })
      }).catch(err => console.error('[Notification Webhook]', err.message));
    } catch (e) {}
  }

  return res.json({ success: true, message: 'Message received successfully', contact_id: contactId });
});

// Admin Inquiries Dashboard & API
app.get('/admin/inquiries', (req, res) => {
  res.sendFile(path.join(__dirname, 'admin-inquiries.html'));
});

app.get('/api/admin/contacts', (req, res) => {
  const secret = req.query.secret || req.headers['x-admin-secret'];
  const ADMIN_SECRET = process.env.ADMIN_SECRET || 'Msrknsds@0304';

  if (secret !== ADMIN_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const contacts = loadJsonDb(CONTACTS_DB_PATH);
  res.json({ contacts });
});

// Legal, Privacy & Policy Pages
app.get('/privacy', (req, res) => {
  res.sendFile(path.join(__dirname, 'privacy.html'));
});

app.get('/terms', (req, res) => {
  res.sendFile(path.join(__dirname, 'terms.html'));
});

app.get('/cookies', (req, res) => {
  res.sendFile(path.join(__dirname, 'telemetry.html'));
});

app.get('/telemetry', (req, res) => {
  res.sendFile(path.join(__dirname, 'telemetry.html'));
});

// Clean SPA Section URLs (No '#' required in browser URL)
const cleanSectionRoutes = [
  '/about', '/contact', '/pricing', '/faq', '/features',
  '/simulator', '/why-nia', '/testimonials', '/comparison', '/quickstart', '/status'
];
cleanSectionRoutes.forEach(route => {
  app.get(route, (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
  });
});

// Single Page Application fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`[NDTechHub] Nia 1.0 distribution & licensing server online at http://localhost:${PORT}`);
});