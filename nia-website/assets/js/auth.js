import { auth, googleProvider } from './firebase-config.js';
import { 
  signInWithPopup, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  onAuthStateChanged,
  signOut
} from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";

// DOM Elements
const loginForm = document.getElementById('login-form');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const googleLoginBtn = document.getElementById('google-login-btn');
const authErrorMsg = document.getElementById('auth-error');
const logoutBtn = document.getElementById('logout-btn');

// Mode toggle (Login vs Signup)
let isLoginMode = true;
const toggleModeBtn = document.getElementById('toggle-mode');
const formTitle = document.getElementById('form-title');
const submitBtn = document.getElementById('submit-btn');

if (toggleModeBtn) {
  toggleModeBtn.addEventListener('click', (e) => {
    e.preventDefault();
    isLoginMode = !isLoginMode;
    if (isLoginMode) {
      formTitle.innerText = "Sign in to NIA";
      submitBtn.innerText = "Sign In";
      toggleModeBtn.innerHTML = "Don't have an account? <b>Sign up</b>";
    } else {
      formTitle.innerText = "Create an Account";
      submitBtn.innerText = "Sign Up";
      toggleModeBtn.innerHTML = "Already have an account? <b>Sign in</b>";
    }
  });
}

// Handle Email/Password Auth
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = emailInput.value;
    const password = passwordInput.value;
    authErrorMsg.style.display = 'none';
    
    try {
      if (isLoginMode) {
        await signInWithEmailAndPassword(auth, email, password);
      } else {
        await createUserWithEmailAndPassword(auth, email, password);
      }
      window.location.href = "dashboard.html";
    } catch (error) {
      authErrorMsg.innerText = error.message;
      authErrorMsg.style.display = 'block';
    }
  });
}

// Handle Google Auth
if (googleLoginBtn) {
  googleLoginBtn.addEventListener('click', async () => {
    authErrorMsg.style.display = 'none';
    try {
      await signInWithPopup(auth, googleProvider);
      window.location.href = "dashboard.html";
    } catch (error) {
      authErrorMsg.innerText = error.message;
      authErrorMsg.style.display = 'block';
    }
  });
}

// Handle Logout
if (logoutBtn) {
  logoutBtn.addEventListener('click', async () => {
    try {
      await signOut(auth);
      window.location.href = "login.html";
    } catch (error) {
      console.error("Error signing out:", error);
    }
  });
}

// Listen for Auth State Changes
export function checkAuthState(requireAuth = false, redirectUrl = "login.html") {
  onAuthStateChanged(auth, (user) => {
    if (user) {
      // User is signed in.
      if (window.location.pathname.endsWith('login.html')) {
        window.location.href = "dashboard.html";
      }
      updateNavbar(user);
    } else {
      // No user is signed in.
      if (requireAuth) {
        window.location.href = redirectUrl;
      }
      updateNavbar(null);
    }
  });
}

function updateNavbar(user) {
  const loginLink = document.getElementById('nav-login-btn');
  const dashboardLink = document.getElementById('nav-dashboard-btn');
  
  if (user) {
    if (loginLink) loginLink.style.display = 'none';
    if (dashboardLink) dashboardLink.style.display = 'inline-block';
  } else {
    if (loginLink) loginLink.style.display = 'inline-block';
    if (dashboardLink) dashboardLink.style.display = 'none';
  }
}
