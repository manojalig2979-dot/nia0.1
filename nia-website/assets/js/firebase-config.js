import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import { getAuth, GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-firestore.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-analytics.js";

// TODO: Replace with your actual Firebase Project Configuration
const firebaseConfig = {
  apiKey: "AIzaSyD9JMvBwBixfUbXGx7FmzV4ULruv6RrSts",
  authDomain: "niaweb.firebaseapp.com",
  projectId: "niaweb",
  storageBucket: "niaweb.firebasestorage.app",
  messagingSenderId: "658030344131",
  appId: "1:658030344131:web:586923e4c597e2fe8b6f76",
  measurementId: "G-R9YNCRFW28"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

// Initialize Firebase services
export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();
