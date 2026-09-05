const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const ACCESS_TOKEN_KEY = "payment_engine_access_token";
const REFRESH_TOKEN_KEY = "payment_engine_refresh_token";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function saveTokens(tokenResponse) {
  localStorage.setItem(
    ACCESS_TOKEN_KEY,
    tokenResponse.access_token,
  );

  localStorage.setItem(
    REFRESH_TOKEN_KEY,
    tokenResponse.refresh_token,
  );
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

async function request(
  path,
  options = {},
  retryOnUnauthorized = true,
) {
  const headers = new Headers(options.headers || {});

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const accessToken = getAccessToken();

  if (accessToken) {
    headers.set(
      "Authorization",
      `Bearer ${accessToken}`,
    );
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers,
    },
  );

  if (
    response.status === 401 &&
    retryOnUnauthorized &&
    getRefreshToken()
  ) {
    try {
      const refreshResponse = await fetch(
        `${API_BASE_URL}/auth/refresh`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            refresh_token: getRefreshToken(),
          }),
        },
      );

      if (refreshResponse.ok) {
        const refreshedTokens =
          await refreshResponse.json();

        saveTokens(refreshedTokens);

        return request(
          path,
          options,
          false,
        );
      }
    } catch {
      clearTokens();
    }
  }

  if (!response.ok) {
    let detail = "Request failed";

    try {
      const errorBody = await response.json();

      detail =
        errorBody.detail ||
        errorBody.message ||
        detail;
    } catch {
      // Keep default error message.
    }

    throw new Error(detail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export async function registerUser(
  email,
  password,
) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
    }),
  });
}

export async function loginUser(
  email,
  password,
) {
  const tokens = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
    }),
  });

  saveTokens(tokens);

  return tokens;
}

export async function createPaymentIntent(
  payment,
) {
  return request("/payments/intents", {
    method: "POST",
    body: JSON.stringify(payment),
  });
}

export async function startTransaction(
  paymentIntentId,
) {
  return request(
    `/transactions/${paymentIntentId}/start`,
    {
      method: "POST",
    },
  );
}

export async function getRiskAssessment(
  transactionId,
) {
  return request(
    `/risk/transactions/${transactionId}`,
  );
}

export async function reconcileTransaction(
  transactionId,
) {
  return request(
    `/reconciliation/transactions/${transactionId}`,
    {
      method: "POST",
    },
  );
}

export async function getMonitoringStatus() {
  return request("/monitoring/status");
}