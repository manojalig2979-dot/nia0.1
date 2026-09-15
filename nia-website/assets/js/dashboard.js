import { auth, db } from './firebase-config.js';
import { checkAuthState } from './auth.js';
import { doc, getDoc, collection, query, where, getDocs } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-firestore.js";

// Ensure the user is logged in before showing the dashboard
checkAuthState(true, "login.html");

const userEmailElem = document.getElementById('user-email');
const userNameElem = document.getElementById('user-name');
const purchaseHistoryContainer = document.getElementById('purchase-history');
const activeLicensesContainer = document.getElementById('active-licenses');

// Listen for the authenticated user object
auth.onAuthStateChanged(async (user) => {
  if (user) {
    if (userEmailElem) userEmailElem.innerText = user.email;
    if (userNameElem) userNameElem.innerText = user.displayName || "NIA User";

    // Fetch user profile data from Firestore
    try {
      // Fetch Purchase History
      await fetchPurchaseHistory(user.email);
      // Fetch Active Licenses
      await fetchActiveLicenses(user.email);
    } catch (error) {
      console.error("Error fetching user data:", error);
    }
  }
});

async function fetchPurchaseHistory(email) {
  if (!purchaseHistoryContainer) return;
  
  // Note: In a real app, you would fetch from a 'purchases' collection
  purchaseHistoryContainer.innerHTML = `
    <div class="p-4 bg-white/5 border border-blue-500/20 rounded-lg mb-3">
      <div class="flex justify-between items-center">
        <div>
          <h4 class="text-white font-bold">NIA Pro License</h4>
          <p class="text-sm text-gray-400">Purchased on Sept 15, 2026</p>
        </div>
        <div class="text-green-400 font-bold">Paid</div>
      </div>
    </div>
  `;
}

async function fetchActiveLicenses(email) {
  if (!activeLicensesContainer) return;

  try {
    const licensesRef = collection(db, "licenses");
    const q = query(licensesRef, where("customer_email", "==", email));
    const querySnapshot = await getDocs(q);

    if (querySnapshot.empty) {
      activeLicensesContainer.innerHTML = `<p class="text-gray-400">No active licenses found for this account.</p>`;
      return;
    }

    let html = '';
    querySnapshot.forEach((doc) => {
      const data = doc.data();
      html += `
        <div class="p-4 bg-white/5 border border-blue-500/20 rounded-lg mb-3">
          <p class="text-sm text-gray-400">License Key:</p>
          <code class="block bg-black/50 p-2 rounded text-blue-400 mt-1 font-mono">${doc.id}</code>
          <p class="text-xs text-gray-500 mt-2">Tier: ${data.tier.toUpperCase()} | Status: ${data.status}</p>
        </div>
      `;
    });
    activeLicensesContainer.innerHTML = html;
  } catch (err) {
    console.error("Firestore error:", err);
    activeLicensesContainer.innerHTML = `
      <div class="p-4 bg-white/5 border border-blue-500/20 rounded-lg mb-3">
        <p class="text-sm text-gray-400">License Key:</p>
        <code class="block bg-black/50 p-2 rounded text-blue-400 mt-1 font-mono">NIA-DEMO-1234-5678</code>
        <p class="text-xs text-gray-500 mt-2">Tier: PRO | Status: active</p>
        <p class="text-xs text-red-400 mt-1">(Demo data - Firestore not connected yet)</p>
      </div>
    `;
  }
}
