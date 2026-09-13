document.addEventListener("DOMContentLoaded", () => {
  // --- MULTI-SCENARIO INTERACTIVE SIMULATOR ---
  const scenarios = [
    {
      id: "scenario-dev",
      title: "Developer & AST Inspection",
      userVoice: '"Nia, project inspect karo aur safe git commit review plan banao."',
      dagNodes: [
        { name: 'inspect_project(path="./nia_agent")', status: "DETECTED: Python AST (64 files)", code: "OK" },
        { name: 'ast_indexer.validate_project()', status: "SYNTAX: Clean, 0 compile errors", code: "VALIDATED" },
        { name: 'git_review.create_change_plan()', status: "DIFF: Unified diff preview generated", code: "APPROVAL_PENDING" },
        { name: 'create_backup(target=".nia_backups")', status: "SNAPSHOT: Rollback state created", code: "SECURED" }
      ],
      niaVoice: '"Aapka project analyze ho gaya hai. AST syntax valid hai aur safe unified diff review plan ready hai!"',
      avatarState: "speaking"
    },
    {
      id: "scenario-whatsapp",
      title: "WhatsApp & Screen Capture",
      userVoice: '"Nia, VS Code ka screenshot lekar team WhatsApp par send karo."',
      dagNodes: [
        { name: 'desktop_tools.focus_window("Visual Studio Code")', status: "HOOK: Target process foregrounded", code: "ACTIVE" },
        { name: 'desktop_tools.capture_screenshot()', status: "FRAME: Local screenshot saved to disk", code: "SAVED" },
        { name: 'whatsapp_manager.dispatch_media(target="Core Team")', status: "SESSION: Dispatched via persistent profile", code: "SENT" }
      ],
      niaVoice: '"VS Code foreground me laakar screenshot le liya hai aur aapke team group par bhej diya hai!"',
      avatarState: "speaking"
    },
    {
      id: "scenario-media",
      title: "System Control & Documents",
      userVoice: '"Nia, background me relaxing lo-fi play karo aur sick leave application draft karo."',
      dagNodes: [
        { name: 'desktop_tools.play_music(genre="relaxing lo-fi")', status: "MEDIA: Streaming lo-fi audio session", code: "PLAYING" },
        { name: 'doc_generator.create_docx(template="leave_letter")', status: "DOCX: Saved to Documents/Leave_Letter.docx", code: "CREATED" },
        { name: 'system_tools.set_volume(level=40)', status: "AUDIO: Windows master volume set to 40%", code: "ADJUSTED" }
      ],
      niaVoice: '"Relaxing lo-fi music start ho gaya hai aur aapka sick leave document ready ho chuka hai!"',
      avatarState: "speaking"
    },
    {
      id: "scenario-diagnostics",
      title: "Self-Healing Diagnostics",
      userVoice: '"Nia, system diagnostics run karo aur mic health verify karo."',
      dagNodes: [
        { name: 'system_diagnostics.check_hardware()', status: "MIC: Active (16000Hz PCM) | Speaker: Ready", code: "HEALTHY" },
        { name: 'system_diagnostics.verify_gemini_api()', status: "AI PROVIDER: Gemini Flash 1.5 latency 128ms", code: "ONLINE" },
        { name: 'system_diagnostics.check_disk_backups()', status: "STORAGE: Rollback protection intact", code: "PASS" }
      ],
      niaVoice: '"Sabhi systems healthy hain! Gemini Flash latency 128ms hai aur microphone calibrated hai."',
      avatarState: "speaking"
    }
  ];

  let currentScenarioIdx = 0;
  let autoPlayInterval = null;
  const terminalScreen = document.getElementById("terminal-screen");
  const scenarioBtns = document.querySelectorAll(".scenario-btn");
  const soundWave = document.getElementById("terminal-soundwave");

  function renderScenario(idx) {
    if (!terminalScreen) return;
    const item = scenarios[idx];

    // Update active tab button style
    scenarioBtns.forEach((btn, bIdx) => {
      if (bIdx === idx) {
        btn.classList.add("border-accentCyan", "text-accentCyan", "bg-cyan-500/10");
        btn.classList.remove("border-white/10", "text-slate-400");
      } else {
        btn.classList.remove("border-accentCyan", "text-accentCyan", "bg-cyan-500/10");
        btn.classList.add("border-white/10", "text-slate-400");
      }
    });

    const dagNodesHtml = item.dagNodes.map((node, i) => `
      <div class="flex items-start justify-between py-1.5 px-3 rounded-lg bg-black/40 border border-white/5 text-xs">
        <div class="flex items-center space-x-2">
          <span class="text-purple-400 font-bold">[DAG Node ${i + 1}]</span>
          <code class="text-slate-300 font-mono">${node.name}</code>
        </div>
        <div class="flex items-center space-x-2">
          <span class="text-slate-400 text-[11px] hidden sm:inline">${node.status}</span>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold ${node.code === 'APPROVAL_PENDING' ? 'bg-yellow-500/20 text-yellow-300' : 'bg-emerald-500/20 text-emerald-400'}">${node.code}</span>
        </div>
      </div>
    `).join("");

    terminalScreen.innerHTML = `
      <!-- User Voice Bubble -->
      <div class="flex items-start space-x-3 p-3 rounded-xl bg-slate-900/60 border border-white/5 transition-all">
        <div class="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
          <i class="fa-solid fa-microphone-lines text-sm"></i>
        </div>
        <div>
          <div class="text-[11px] font-mono text-emerald-400 uppercase tracking-wide">User Voice Input (Hindi / Hinglish)</div>
          <p class="text-sm font-medium text-white mt-0.5">${item.userVoice}</p>
        </div>
      </div>

      <!-- Execution DAG Graph -->
      <div class="space-y-2 pt-2">
        <div class="flex items-center justify-between text-[11px] font-mono text-slate-400 px-1">
          <span>DETERMINISTIC OS PIPELINE</span>
          <span class="text-accentCyan">LOCAL RUNTIME</span>
        </div>
        <div class="space-y-1.5 pl-2 border-l-2 border-accentPurple">
          ${dagNodesHtml}
        </div>
      </div>

      <!-- Nia Voice Response -->
      <div class="flex items-start space-x-3 p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-500/20 transition-all">
        <div class="w-8 h-8 rounded-lg bg-cyan-400/20 text-accentCyan flex items-center justify-center shrink-0">
          <i class="fa-solid fa-robot text-sm"></i>
        </div>
        <div class="flex-1">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-mono text-accentCyan uppercase tracking-wide">Nia (Swara Neural Voice)</span>
            <span class="text-[10px] text-slate-400 font-mono">140ms Latency</span>
          </div>
          <p class="text-sm font-medium text-cyan-200 mt-0.5">${item.niaVoice}</p>
        </div>
      </div>
    `;

    // Pulse soundwave
    if (soundWave) {
      soundWave.style.opacity = "1";
    }
  }

  // Setup scenario clicks
  scenarioBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      clearInterval(autoPlayInterval);
      const targetIdx = parseInt(btn.getAttribute("data-index") || "0", 10);
      currentScenarioIdx = targetIdx;
      renderScenario(currentScenarioIdx);
      startAutoPlay();
    });
  });

  function startAutoPlay() {
    autoPlayInterval = setInterval(() => {
      currentScenarioIdx = (currentScenarioIdx + 1) % scenarios.length;
      renderScenario(currentScenarioIdx);
    }, 7500);
  }

  // Initialize Simulator
  if (terminalScreen) {
    renderScenario(0);
    startAutoPlay();
  }

  // --- QUICKSTART TABS ---
  const quickstartBtns = document.querySelectorAll(".qs-tab-btn");
  const quickstartContents = document.querySelectorAll(".qs-tab-content");

  quickstartBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-tab");
      quickstartBtns.forEach(b => {
        b.classList.remove("border-accentCyan", "text-accentCyan", "bg-cyan-500/10");
        b.classList.add("border-transparent", "text-slate-400");
      });
      btn.classList.add("border-accentCyan", "text-accentCyan", "bg-cyan-500/10");
      btn.classList.remove("border-transparent", "text-slate-400");

      quickstartContents.forEach(c => {
        if (c.id === target) {
          c.classList.remove("hidden");
        } else {
          c.classList.add("hidden");
        }
      });
    });
  });

  // --- COPY CODE BUTTONS ---
  const copyBtns = document.querySelectorAll(".copy-btn");
  copyBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const textToCopy = btn.getAttribute("data-code");
      if (textToCopy) {
        navigator.clipboard.writeText(textToCopy).then(() => {
          const original = btn.innerHTML;
          btn.innerHTML = '<i class="fa-solid fa-check text-accentCyan mr-1"></i> Copied!';
          setTimeout(() => {
            btn.innerHTML = original;
          }, 2000);
        });
      }
    });
  });

  // --- DOWNLOAD MODAL INTERACTION ---
  const downloadModal = document.getElementById("download-modal");
  const modalTriggers = document.querySelectorAll(".open-download-modal");
  const closeBtn = document.getElementById("close-download-modal");

  modalTriggers.forEach((trigger) => {
    trigger.addEventListener("click", (e) => {
      e.preventDefault();
      if (downloadModal) {
        downloadModal.classList.remove("hidden");
        downloadModal.classList.add("flex");
      }
    });
  });

  if (closeBtn && downloadModal) {
    closeBtn.addEventListener("click", () => {
      downloadModal.classList.add("hidden");
      downloadModal.classList.remove("flex");
    });

    downloadModal.addEventListener("click", (e) => {
      if (e.target === downloadModal) {
        downloadModal.classList.add("hidden");
        downloadModal.classList.remove("flex");
      }
    });
  }

  // --- BUY PRO LICENSE MODAL INTERACTION ---
  const buyModal = document.getElementById("buy-modal");
  const buyTriggers = document.querySelectorAll(".open-buy-modal");
  const closeBuyBtn = document.getElementById("close-buy-modal");
  const licenseForm = document.getElementById("license-purchase-form");
  const licenseBox = document.getElementById("license-generated-box");
  const keyDisplay = document.getElementById("generated-key-display");
  const modalTierTitle = document.getElementById("modal-tier-title");
  const modalTierPrice = document.getElementById("modal-tier-price");
  const modalTierDesc = document.getElementById("modal-tier-desc");
  const payBtnText = document.getElementById("pay-btn-text");
  const selectedTierInput = document.getElementById("selected-tier-input");

  const tierConfigs = {
    test_flight: {
      title: "7-Day Pro Test Flight",
      price: "₹99 INR / $1 USD (7 Days)",
      desc: "Instant full access to all Pro features. Test WhatsApp automation, AST coding copilot, and 3D talking companion on your PC. Cancel anytime with 1 click.",
      btnText: "Start 7-Day Test Flight (₹99 / $1)"
    },
    starter: {
      title: "Nia Starter / Personal",
      price: "₹899 / mo ($12 USD)",
      desc: "Daily desktop voice companion, unlimited local OS tools, Michi Bot 3D avatar, and 500 smart-agent cloud tasks included each month.",
      btnText: "Subscribe to Starter (₹899/mo)"
    },
    pro: {
      title: "Nia Pro Power Agent",
      price: "₹1,799 / mo ($24 USD)",
      desc: "For developers & professionals: unlimited WhatsApp workflows, AST multi-file code inspection, safe Git diff review, and encrypted persistent memory.",
      btnText: "Subscribe to Pro Agent (₹1,799/mo)"
    },
    lifetime_byok: {
      title: "Lifetime Desktop Pass (BYOK)",
      price: "₹6,999 INR / $99 USD (One-Time)",
      desc: "Own the Nia Desktop software forever. Plug in your own free Google Gemini or OpenAI API key. Zero monthly fees and zero server costs.",
      btnText: "Get Lifetime BYOK Pass (₹6,999)"
    }
  };

  buyTriggers.forEach((trigger) => {
    trigger.addEventListener("click", (e) => {
      e.preventDefault();
      const tier = trigger.getAttribute("data-tier") || "pro";
      const config = tierConfigs[tier] || tierConfigs.pro;

      if (modalTierTitle) modalTierTitle.textContent = config.title;
      if (modalTierPrice) modalTierPrice.textContent = config.price;
      if (modalTierDesc) modalTierDesc.textContent = config.desc;
      if (payBtnText) payBtnText.textContent = config.btnText;
      if (selectedTierInput) selectedTierInput.value = tier;

      // Reset box state
      if (licenseForm) licenseForm.classList.remove("hidden");
      if (licenseBox) licenseBox.classList.add("hidden");

      if (downloadModal) {
        downloadModal.classList.add("hidden");
        downloadModal.classList.remove("flex");
      }

      if (buyModal) {
        buyModal.classList.remove("hidden");
        buyModal.classList.add("flex");
      }
    });
  });

  if (closeBuyBtn && buyModal) {
    closeBuyBtn.addEventListener("click", () => {
      buyModal.classList.add("hidden");
      buyModal.classList.remove("flex");
    });

    buyModal.addEventListener("click", (e) => {
      if (e.target === buyModal) {
        buyModal.classList.add("hidden");
        buyModal.classList.remove("flex");
      }
    });
  }

  if (licenseForm) {
    licenseForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("buyer-email").value.trim();
      const tier = selectedTierInput ? selectedTierInput.value : "pro";
      const payBtn = document.getElementById("pay-button");
      payBtn.disabled = true;
      payBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Initializing Secure Checkout...';

      try {
        const response = await fetch('/api/license/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            secret: 'ndtechhub_checkout_demo_2026',
            customer_email: email,
            tier: tier
          })
        });
        const data = await response.json();
        if (data.license_key) {
          licenseForm.classList.add("hidden");
          licenseBox.classList.remove("hidden");
          keyDisplay.textContent = data.license_key;
        } else {
          alert("License generation failed. Please contact support@ndtechhub.com");
        }
      } catch (err) {
        alert("Payment gateway connection error: " + err.message);
      } finally {
        payBtn.disabled = false;
        payBtn.innerHTML = '<i class="fa-solid fa-lock mr-2"></i> <span id="pay-btn-text">Proceed to Checkout</span>';
      }
    });
  }

  // --- CONTACT FORM SUBMISSION ---
  const contactForm = document.getElementById("contact-form");
  const contactSuccessMsg = document.getElementById("contact-success-msg");
  if (contactForm) {
    contactForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById("contact-submit-btn");
      const name = document.getElementById("contact-name").value.trim();
      const email = document.getElementById("contact-email").value.trim();
      const inquiryType = document.getElementById("contact-inquiry-type").value;
      const subject = document.getElementById("contact-subject").value.trim();
      const message = document.getElementById("contact-message").value.trim();

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Sending to Engineering...';
      }

      try {
        const response = await fetch('/api/contact', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: name,
            email: email,
            inquiry_type: inquiryType,
            subject: subject,
            message: message
          })
        });
        const result = await response.json();
        if (result.success) {
          contactForm.classList.add("hidden");
          if (contactSuccessMsg) {
            contactSuccessMsg.classList.remove("hidden");
            if (typeof lucide !== 'undefined') {
              lucide.createIcons();
            }
          }
        } else {
          alert(result.error || "Submission failed. Please email us directly at support@ndtechhub.com");
        }
      } catch (err) {
        contactForm.classList.add("hidden");
        if (contactSuccessMsg) {
          contactSuccessMsg.classList.remove("hidden");
        }
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
        }
      }
    });
  }

  // --- MOBILE MENU TOGGLE ---
  const mobileMenuBtn = document.getElementById("mobile-menu-btn");
  const mobileMenu = document.getElementById("mobile-menu");
  if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener("click", () => {
      mobileMenu.classList.toggle("hidden");
    });
  }

  // --- CLEAN URL ROUTING (NO '#' IN BROWSER URL) ---
  const routeSectionMap = {
    '/why-nia': 'why-nia',
    '/simulator': 'simulator',
    '/features': 'features',
    '/about': 'about',
    '/pricing': 'pricing',
    '/faq': 'faq',
    '/contact': 'contact',
    '/testimonials': 'testimonials',
    '/comparison': 'comparison',
    '/quickstart': 'quickstart',
    '/status': 'status'
  };

  function scrollToSection(sectionId, updateUrlPath) {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      if (updateUrlPath) {
        history.pushState(null, '', updateUrlPath);
      }
      // Update active bento pills
      document.querySelectorAll('.bento-pill').forEach(pill => {
        const href = pill.getAttribute('href');
        if (href === updateUrlPath) {
          pill.classList.add('active');
        } else {
          pill.classList.remove('active');
        }
      });
    }
  }

  // Handle clicks on navigation links
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (!link) return;
    const href = link.getAttribute('href');
    if (!href) return;

    // If link is a clean route
    if (routeSectionMap[href]) {
      e.preventDefault();
      scrollToSection(routeSectionMap[href], href);
      if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
        mobileMenu.classList.add('hidden');
      }
      return;
    }

    // If link is an old #hash anchor, convert to clean URL
    if (href.startsWith('#')) {
      const sectionId = href.substring(1);
      const matchingPath = Object.keys(routeSectionMap).find(k => routeSectionMap[k] === sectionId);
      if (matchingPath) {
        e.preventDefault();
        scrollToSection(sectionId, matchingPath);
        if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
          mobileMenu.classList.add('hidden');
        }
      }
    }
  });

  // Handle direct initial load of clean URL (e.g. user visits /pricing or /about directly)
  const currentPath = window.location.pathname.replace(/\/$/, "");
  if (routeSectionMap[currentPath]) {
    setTimeout(() => {
      scrollToSection(routeSectionMap[currentPath], null);
    }, 180);
  }

  // Handle browser back/forward buttons
  window.addEventListener('popstate', () => {
    const path = window.location.pathname.replace(/\/$/, "");
    if (routeSectionMap[path]) {
      scrollToSection(routeSectionMap[path], null);
    }
  });
});