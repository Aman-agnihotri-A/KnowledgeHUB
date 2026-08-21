const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "";

const SESSION_KEY = "knowledgehub_session";

function getStoredSession() {
  const raw = sessionStorage.getItem(
    SESSION_KEY,
  );

  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    sessionStorage.removeItem(
      SESSION_KEY,
    );

    return null;
  }
}

function decodeJwtPayload(token) {
  const parts = token.split(".");

  if (parts.length !== 3) {
    throw new Error(
      "Invalid authentication token.",
    );
  }

  const base64 = parts[1]
    .replace(/-/g, "+")
    .replace(/_/g, "/");

  const padded =
    base64 +
    "=".repeat(
      (4 - (base64.length % 4)) % 4,
    );

  try {
    return JSON.parse(
      atob(padded),
    );
  } catch {
    throw new Error(
      "Invalid authentication token.",
    );
  }
}

function createSession(
  accessToken,
  tokenType,
) {
  const payload =
    decodeJwtPayload(accessToken);

  const session = {
    accessToken,
    tokenType: tokenType || "bearer",
    userId: payload.sub,
    role: payload.role,
    tenantId: payload.tenant_id,
  };

  sessionStorage.setItem(
    SESSION_KEY,
    JSON.stringify(session),
  );

  return session;
}

export function getSession() {
  return getStoredSession();
}

export function clearSession() {
  sessionStorage.removeItem(
    SESSION_KEY,
  );
}

async function request(
  path,
  options = {},
) {
  const session =
    getStoredSession();

  const headers = new Headers(
    options.headers || {},
  );

  if (options.body !== undefined) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  if (session?.accessToken) {
    headers.set(
      "Authorization",
      `Bearer ${session.accessToken}`,
    );
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers,
    },
  );

  if (response.status === 401) {
    clearSession();

    throw new Error(
      "Your session has expired. Please log in again.",
    );
  }

  if (!response.ok) {
    let message =
      "Request failed.";

    try {
      const body =
        await response.json();

      if (
        typeof body.detail ===
        "string"
      ) {
        message = body.detail;
      }
    } catch {
      // Keep the default error.
    }

    throw new Error(message);
  }

  if (
    response.status === 204
  ) {
    return null;
  }

  return response.json();
}

export async function login(
  email,
  password,
) {
  const response =
    await request(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
        }),
      },
    );

  return createSession(
    response.access_token,
    response.token_type,
  );
}

export async function listTenants() {
  return request("/tenants");
}

export async function createTenant(
  tenant,
) {
  return request(
    "/tenants",
    {
      method: "POST",
      body: JSON.stringify(tenant),
    },
  );
}

export async function listConversations(
  tenantId,
) {
  return request(
    `/conversations/${tenantId}`,
  );
}

export async function createConversation(
  tenantId,
  title = null,
) {
  return request(
    `/conversations/${tenantId}`,
    {
      method: "POST",
      body: JSON.stringify({
        title,
      }),
    },
  );
}

export async function getConversation(
  tenantId,
  conversationId,
) {
  return request(
    `/conversations/${tenantId}/${conversationId}`,
  );
}

export async function askQuestion(
  tenantId,
  question,
  conversationId,
) {
  return request(
    `/rag/${tenantId}/ask`,
    {
      method: "POST",
      body: JSON.stringify({
        question,
        top_k: 5,
        conversation_id:
          conversationId,
      }),
    },
  );
}
export async function listDocuments(
  tenantId,
) {
  return request(
    `/documents/${tenantId}`,
  );
}

async function uploadRequest(
  path,
  file,
) {
  const session =
    getStoredSession();

  const headers = new Headers();

  if (session?.accessToken) {
    headers.set(
      "Authorization",
      `Bearer ${session.accessToken}`,
    );
  }

  const formData = new FormData();

  formData.append(
    "file",
    file,
  );

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      method: "POST",
      headers,
      body: formData,
    },
  );

  if (response.status === 401) {
    clearSession();

    throw new Error(
      "Your session has expired. Please log in again.",
    );
  }

  if (!response.ok) {
    let message =
      "Document upload failed.";

    try {
      const body =
        await response.json();

      if (
        typeof body.detail ===
        "string"
      ) {
        message = body.detail;
      }
    } catch {
      // Keep default error.
    }

    throw new Error(message);
  }

  return response.json();
}

export async function uploadDocument(
  tenantId,
  file,
) {
  return uploadRequest(
    `/documents/${tenantId}/upload`,
    file,
  );
}

export async function processDocument(
  tenantId,
  documentId,
) {
  return request(
    `/documents/${tenantId}/${documentId}/process`,
    {
      method: "POST",
    },
  );
}

export async function listTenantUsers(
  tenantId,
) {
  return request(
    `/tenants/${tenantId}/users`,
  );
}

export async function createTenantUser(
  tenantId,
  user,
) {
  return request(
    `/tenants/${tenantId}/users`,
    {
      method: "POST",
      body: JSON.stringify(user),
    },
  );
}

export async function updateTenantUserStatus(
  tenantId,
  userId,
  isActive,
) {
  return request(
    `/tenants/${tenantId}/users/${userId}/status`,
    {
      method: "PATCH",
      body: JSON.stringify({
        is_active: isActive,
      }),
    },
  );
}