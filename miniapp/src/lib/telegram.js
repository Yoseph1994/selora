/**
 * Telegram WebApp & Serverless SDK Utilities
 */

export function isTelegramWebApp() {
  return typeof window !== 'undefined' && Boolean(window.Telegram?.WebApp?.initData);
}

export function getTelegramWebApp() {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    return window.Telegram.WebApp;
  }
  return null;
}

export function getTelegramUser() {
  const tg = getTelegramWebApp();
  if (tg?.initDataUnsafe?.user) {
    return tg.initDataUnsafe.user;
  }
  return {
    id: 12345678,
    first_name: 'Customer',
    username: ''
  };
}

export function triggerHaptic(type = 'medium') {
  const tg = getTelegramWebApp();
  if (!tg?.HapticFeedback) return;
  try {
    if (type === 'light' || type === 'medium' || type === 'heavy') {
      tg.HapticFeedback.impactOccurred(type);
    } else if (type === 'success' || type === 'warning' || type === 'error') {
      tg.HapticFeedback.notificationOccurred(type);
    } else if (type === 'selection') {
      tg.HapticFeedback.selectionChanged();
    }
  } catch (e) {
    // Graceful fallback
  }
}

/**
 * Call a Telegram Serverless backend endpoint (tgcloud/endpoints/<name>.js)
 * Automatically utilizes Telegram.WebApp.Serverless.call when deployed in Telegram,
 * with seamless fallback for local browser testing.
 */
export async function callServerless(endpoint, payload = {}) {
  const tg = getTelegramWebApp();

  // 1. Native Telegram Serverless RPC
  if (tg?.Serverless?.call) {
    return new Promise((resolve, reject) => {
      tg.Serverless.call(endpoint, payload, (err, result) => {
        if (err) {
          console.error(`Telegram Serverless RPC error [${endpoint}]:`, err);
          reject(err);
        } else {
          resolve(result);
        }
      });
    });
  }

  // 2. Direct HTTP endpoint fallback (served by tgcloud at /api/<endpoint>)
  try {
    const res = await fetch(`/api/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      const data = await res.json();
      return data.result || data;
    }
  } catch (e) {
    // Continue to mock fallback
  }

  // 3. Fallback mock for local development and preview
  console.info(`[Dev Mode] Emulating Serverless call for: ${endpoint}`);
  if (endpoint === 'getSettings') {
    return {
      ok: true,
      storeName: 'Selora Prints',
      cbeAccount: '1000492813589',
      cbeName: 'KEBROM HAILU',
      telebirrAccount: '0947702896',
      telebirrName: 'KEBROM HAILU',
      supportUsername: 'Keb_g',
      depositRate: 0.50,
      storeLocation: 'Ledeta, Addis Ababa'
    };
  }

  if (endpoint === 'createOrder') {
    const randomCode = `SP-${Math.floor(1000 + Math.random() * 9000)}`;
    return {
      ok: true,
      orderCode: randomCode,
      totalEtb: payload.totalEtb,
      depositEtb: Math.round(payload.totalEtb * 0.50),
      balanceEtb: Math.round(payload.totalEtb * 0.50),
      status: 'pending_review'
    };
  }

  if (endpoint === 'trackOrder') {
    return {
      ok: true,
      order: {
        orderCode: payload.orderCode || 'SP-1003',
        items: '100x Business Cards (Double Sided)',
        totalEtb: 1500,
        depositEtb: 750,
        balanceEtb: 750,
        deliveryType: 'Taxi / Yango Delivery',
        deliveryLocation: 'Bole Atlas',
        status: 'in_production',
        paymentStatus: 'approved',
        deadline: '2026-11-20',
        createdAt: new Date().toISOString()
      }
    };
  }

  return { ok: true };
}
