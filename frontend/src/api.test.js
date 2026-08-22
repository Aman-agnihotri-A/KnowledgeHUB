import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";



import {
  listDocuments,
  processDocument,
  uploadDocument,
  askQuestion,
  clearSession,
  getSession,
  login,
  downloadDocument,
  createTenant,
  listTenants,
  createTenantUser,
  listTenantUsers,
  updateTenantUserStatus,
} from "./api";

describe("frontend API client", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("lists documents using a status filter", async () => {
  const token =
    createTestJwt({
      sub: "admin-1",
      role: "tenant_admin",
      tenant_id: "tenant-1",
    });

  sessionStorage.setItem(
    "knowledgehub_session",
    JSON.stringify({
      accessToken: token,
      tokenType: "bearer",
      userId: "admin-1",
      role: "tenant_admin",
      tenantId: "tenant-1",
    }),
  );

  const fetchMock =
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: "document-1",
            tenant_id: "tenant-1",
            filename: "guide.pdf",
            status: "ready",
          },
        ]),
        {
          status: 200,
          headers: {
            "Content-Type":
              "application/json",
          },
        },
      ),
    );

  vi.stubGlobal(
    "fetch",
    fetchMock,
  );

  const result =
    await listDocuments(
      "tenant-1",
      "ready",
    );

  expect(result).toHaveLength(1);

  expect(
    fetchMock,
  ).toHaveBeenCalledWith(
    "/documents/tenant-1?status=ready",
    expect.objectContaining({
      headers:
        expect.any(Headers),
    }),
  );
});

it("downloads a tenant document using the authenticated session", async () => {
  const token =
    createTestJwt({
      sub: "user-1",
      role: "sub_user",
      tenant_id: "tenant-1",
    });

  sessionStorage.setItem(
    "knowledgehub_session",
    JSON.stringify({
      accessToken: token,
      tokenType: "bearer",
      userId: "user-1",
      role: "sub_user",
      tenantId: "tenant-1",
    }),
  );

  const blob =
    new Blob(
      ["KnowledgeHub document"],
      {
        type: "application/pdf",
      },
    );

  const fetchMock =
    vi.fn().mockResolvedValue(
      new Response(blob, {
        status: 200,
        headers: {
          "Content-Type":
            "application/pdf",
          "Content-Disposition":
            'attachment; filename="guide.pdf"',
        },
      }),
    );

  vi.stubGlobal(
    "fetch",
    fetchMock,
  );

  const createObjectUrl =
    vi.fn().mockReturnValue(
      "blob:test",
    );

  const revokeObjectUrl =
    vi.fn();

  vi.spyOn(
    URL,
    "createObjectURL",
    ).mockReturnValue(
    "blob:test",
    );

    vi.spyOn(
    URL,
    "revokeObjectURL",
    ).mockImplementation(
    () => {},
    );

  const appendChild =
    document.body.appendChild;

  const remove =
    vi.fn();

  const click =
    vi.fn();

  vi.spyOn(
    document,
    "createElement",
  ).mockReturnValue({
    href: "",
    download: "",
    click,
    remove,
  });

  await downloadDocument(
    "tenant-1",
    "document-1",
  );

  expect(
    fetchMock,
  ).toHaveBeenCalledWith(
    "/documents/tenant-1/document-1/download",
    expect.objectContaining({
      method: "GET",
      headers:
        expect.any(Headers),
    }),
  );

  expect(
    fetchMock.mock.calls[0][1]
      .headers.get(
        "Authorization",
      ),
  ).toBe(
    `Bearer ${token}`,
  );

  expect(
    createObjectUrl,
  ).toHaveBeenCalledWith(
    blob,
  );

  expect(click).toHaveBeenCalled();

  expect(
    revokeObjectUrl,
  ).toHaveBeenCalledWith(
    "blob:test",
  );

  document.body.appendChild =
    appendChild;
});

  it("lists tenants for a Super Admin", async () => {
  const token =
    createTestJwt({
      sub: "super-admin-1",
      role: "super_admin",
      tenant_id: null,
    });

  sessionStorage.setItem(
    "knowledgehub_session",
    JSON.stringify({
      accessToken: token,
      tokenType: "bearer",
      userId: "super-admin-1",
      role: "super_admin",
      tenantId: null,
    }),
  );

  const fetchMock =
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: "tenant-1",
            name: "Acme Corp",
            slug: "acme",
            is_active: true,
          },
        ]),
        {
          status: 200,
          headers: {
            "Content-Type":
              "application/json",
          },
        },
      ),
    );

  vi.stubGlobal(
    "fetch",
    fetchMock,
  );

  const result =
    await listTenants();

  expect(result).toHaveLength(1);

  expect(result[0]).toEqual({
    id: "tenant-1",
    name: "Acme Corp",
    slug: "acme",
    is_active: true,
  });

  expect(
    fetchMock,
  ).toHaveBeenCalledWith(
    "/tenants",
    expect.objectContaining({
      headers:
        expect.any(Headers),
    }),
  );

  expect(
    fetchMock.mock.calls[0][1]
      .headers.get("Authorization"),
  ).toBe(
    `Bearer ${token}`,
  );
});

it("creates a tenant for a Super Admin", async () => {
  const token =
    createTestJwt({
      sub: "super-admin-1",
      role: "super_admin",
      tenant_id: null,
    });

  sessionStorage.setItem(
    "knowledgehub_session",
    JSON.stringify({
      accessToken: token,
      tokenType: "bearer",
      userId: "super-admin-1",
      role: "super_admin",
      tenantId: null,
    }),
  );

  const fetchMock =
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "tenant-2",
          name: "New Tenant",
          slug: "new-tenant",
          is_active: true,
        }),
        {
          status: 201,
          headers: {
            "Content-Type":
              "application/json",
          },
        },
      ),
    );

  vi.stubGlobal(
    "fetch",
    fetchMock,
  );

  const result =
    await createTenant({
      name: "New Tenant",
      slug: "new-tenant",
    });

  expect(result).toEqual({
    id: "tenant-2",
    name: "New Tenant",
    slug: "new-tenant",
    is_active: true,
  });

  const [
    url,
    options,
  ] =
    fetchMock.mock.calls[0];

  expect(url).toBe(
    "/tenants",
  );

  expect(options.method).toBe(
    "POST",
  );

  expect(
    JSON.parse(options.body),
  ).toEqual({
    name: "New Tenant",
    slug: "new-tenant",
  });

  expect(
    options.headers.get(
      "Authorization",
    ),
  ).toBe(
    `Bearer ${token}`,
  );
});

  it("lists tenant users", async () => {
  const token =
    createTestJwt({
      sub: "admin-1",
      role: "tenant_admin",
      tenant_id: "tenant-1",
    });

  sessionStorage.setItem(
    "knowledgehub_session",
    JSON.stringify({
      accessToken: token,
      tokenType: "bearer",
      userId: "admin-1",
      role: "tenant_admin",
      tenantId: "tenant-1",
    }),
  );

  const fetchMock =
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: "user-1",
            email:
              "user@knowledgehub.local",
            full_name: "Demo User",
            role: "sub_user",
            tenant_id: "tenant-1",
            is_active: true,
          },
        ]),
        {
          status: 200,
          headers: {
            "Content-Type":
              "application/json",
          },
        },
      ),
    );

  vi.stubGlobal(
    "fetch",
    fetchMock,
  );

  const result =
    await listTenantUsers(
      "tenant-1",
    );

  expect(result).toHaveLength(1);
  expect(result[0].role).toBe(
    "sub_user",
  );

  expect(
    fetchMock,
  ).toHaveBeenCalledWith(
    "/tenants/tenant-1/users",
    expect.objectContaining({
      headers:
        expect.any(Headers),
    }),
  );
});

it("creates a Sub User", async () => {
  const token =
    createTestJwt({
      sub: "admin-1",
      role: "tenant_admin",
      tenant_id: "tenant-1",
    });

  sessionStorage.setItem(
    "knowledgehub_session",
    JSON.stringify({
      accessToken: token,
      tokenType: "bearer",
      userId: "admin-1",
      role: "tenant_admin",
      tenantId: "tenant-1",
    }),
  );

  const fetchMock =
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "user-2",
          email:
            "newuser@knowledgehub.local",
          full_name: "New User",
          role: "sub_user",
          tenant_id: "tenant-1",
          is_active: true,
        }),
        {
          status: 201,
          headers: {
            "Content-Type":
              "application/json",
          },
        },
      ),
    );

  vi.stubGlobal(
    "fetch",
    fetchMock,
  );

  const result =
    await createTenantUser(
      "tenant-1",
      {
        email:
          "newuser@knowledgehub.local",
        password:
          "SubUser@123",
        full_name: "New User",
        role: "sub_user",
      },
    );

  expect(result.email).toBe(
    "newuser@knowledgehub.local",
  );

  const [
    url,
    options,
  ] =
    fetchMock.mock.calls[0];

  expect(url).toBe(
    "/tenants/tenant-1/users",
  );

  expect(options.method).toBe(
    "POST",
  );

  expect(
    JSON.parse(options.body),
  ).toEqual({
    email:
      "newuser@knowledgehub.local",
    password:
      "SubUser@123",
    full_name: "New User",
    role: "sub_user",
  });

  expect(
    options.headers.get(
      "Authorization",
    ),
  ).toBe(
    `Bearer ${token}`,
  );
});

it("updates tenant user status", async () => {
  const token =
    createTestJwt({
      sub: "admin-1",
      role: "tenant_admin",
      tenant_id: "tenant-1",
    });

  sessionStorage.setItem(
    "knowledgehub_session",
    JSON.stringify({
      accessToken: token,
      tokenType: "bearer",
      userId: "admin-1",
      role: "tenant_admin",
      tenantId: "tenant-1",
    }),
  );

  const fetchMock =
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "user-1",
          email:
            "user@knowledgehub.local",
          full_name: "Demo User",
          role: "sub_user",
          tenant_id: "tenant-1",
          is_active: false,
        }),
        {
          status: 200,
          headers: {
            "Content-Type":
              "application/json",
          },
        },
      ),
    );

  vi.stubGlobal(
    "fetch",
    fetchMock,
  );

  const result =
    await updateTenantUserStatus(
      "tenant-1",
      "user-1",
      false,
    );

  expect(
    result.is_active,
  ).toBe(false);

  const [
    url,
    options,
  ] =
    fetchMock.mock.calls[0];

  expect(url).toBe(
    "/tenants/tenant-1/users/user-1/status",
  );

  expect(options.method).toBe(
    "PATCH",
  );

  expect(
    JSON.parse(options.body),
  ).toEqual({
    is_active: false,
  });
});

  it("lists tenant documents", async () => {
  const token =
    createTestJwt({
      sub: "admin-1",
      role: "tenant_admin",
      tenant_id: "tenant-1",
    });

  sessionStorage.setItem(
    "knowledgehub_session",
    JSON.stringify({
      accessToken: token,
      tokenType: "bearer",
      userId: "admin-1",
      role: "tenant_admin",
      tenantId: "tenant-1",
    }),
  );

  const fetchMock = vi
    .fn()
    .mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: "document-1",
            tenant_id: "tenant-1",
            filename:
              "KnowledgeHub_Demo_Product_Guide.pdf",
            status: "ready",
          },
        ]),
        {
          status: 200,
          headers: {
            "Content-Type":
              "application/json",
          },
        },
      ),
    );

  vi.stubGlobal(
    "fetch",
    fetchMock,
  );

  const result =
    await listDocuments(
      "tenant-1",
    );

  expect(result).toHaveLength(1);

  expect(
    fetchMock,
  ).toHaveBeenCalledWith(
    "/documents/tenant-1",
    expect.objectContaining({
      headers:
        expect.any(Headers),
    }),
  );
});

it("uploads a document as multipart form data", async () => {
  const token =
    createTestJwt({
      sub: "admin-1",
      role: "tenant_admin",
      tenant_id: "tenant-1",
    });

  sessionStorage.setItem(
    "knowledgehub_session",
    JSON.stringify({
      accessToken: token,
      tokenType: "bearer",
      userId: "admin-1",
      role: "tenant_admin",
      tenantId: "tenant-1",
    }),
  );

  const fetchMock = vi
    .fn()
    .mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "document-1",
          tenant_id: "tenant-1",
          filename:
            "KnowledgeHub_Demo_Product_Guide.pdf",
          status: "uploaded",
        }),
        {
          status: 201,
          headers: {
            "Content-Type":
              "application/json",
          },
        },
      ),
    );

  vi.stubGlobal(
    "fetch",
    fetchMock,
  );

  const file = new File(
    ["pdf-content"],
    "KnowledgeHub_Demo_Product_Guide.pdf",
    {
      type: "application/pdf",
    },
  );

  const result =
    await uploadDocument(
      "tenant-1",
      file,
    );

  expect(
    result.filename,
  ).toBe(
    "KnowledgeHub_Demo_Product_Guide.pdf",
  );

  const [
    url,
    options,
  ] = fetchMock.mock.calls[0];

  expect(url).toBe(
    "/documents/tenant-1/upload",
  );

  expect(options.method).toBe(
    "POST",
  );

  expect(
    options.headers.get(
      "Authorization",
    ),
  ).toBe(
    `Bearer ${token}`,
  );

  expect(
    options.headers.has(
      "Content-Type",
    ),
  ).toBe(false);

  expect(
    options.body,
  ).toBeInstanceOf(FormData);

  expect(
    options.body.get("file").name,
  ).toBe(
    "KnowledgeHub_Demo_Product_Guide.pdf",
  );
});

it("processes a tenant document", async () => {
  const token =
    createTestJwt({
      sub: "admin-1",
      role: "tenant_admin",
      tenant_id: "tenant-1",
    });

  sessionStorage.setItem(
    "knowledgehub_session",
    JSON.stringify({
      accessToken: token,
      tokenType: "bearer",
      userId: "admin-1",
      role: "tenant_admin",
      tenantId: "tenant-1",
    }),
  );

  const fetchMock = vi
    .fn()
    .mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "document-1",
          tenant_id: "tenant-1",
          filename:
            "KnowledgeHub_Demo_Product_Guide.pdf",
          status: "ready",
        }),
        {
          status: 200,
          headers: {
            "Content-Type":
              "application/json",
          },
        },
      ),
    );

  vi.stubGlobal(
    "fetch",
    fetchMock,
  );

  const result =
    await processDocument(
      "tenant-1",
      "document-1",
    );

  expect(
    result.status,
  ).toBe("ready");

  expect(
    fetchMock,
  ).toHaveBeenCalledWith(
    "/documents/tenant-1/document-1/process",
    expect.objectContaining({
      method: "POST",
    }),
  );
});

  afterEach(() => {
    sessionStorage.clear();
  });

  it("stores authentication session after login", async () => {
    const token =
      createTestJwt({
        sub: "user-1",
        role: "sub_user",
        tenant_id: "tenant-1",
      });

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            access_token: token,
            token_type: "bearer",
          }),
          {
            status: 200,
            headers: {
              "Content-Type":
                "application/json",
            },
          },
        ),
      ),
    );

    const session =
      await login(
        "user@example.com",
        "password",
      );

    expect(
      session.accessToken,
    ).toBe(token);

    expect(
      session.userId,
    ).toBe("user-1");

    expect(
      session.role,
    ).toBe("sub_user");

    expect(
      session.tenantId,
    ).toBe("tenant-1");

    expect(
      getSession(),
    ).toEqual(session);
  });

  it("sends authenticated RAG requests", async () => {
    const token =
      createTestJwt({
        sub: "user-1",
        role: "sub_user",
        tenant_id: "tenant-1",
      });

    sessionStorage.setItem(
      "knowledgehub_session",
      JSON.stringify({
        accessToken: token,
        tokenType: "bearer",
        userId: "user-1",
        role: "sub_user",
        tenantId: "tenant-1",
      }),
    );

    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            question: "What is this?",
            answer: "This is KnowledgeHub.",
            abstained: false,
            sources: [],
            conversation_id:
              "conversation-1",
          }),
          {
            status: 200,
            headers: {
              "Content-Type":
                "application/json",
            },
          },
        ),
      );

    vi.stubGlobal(
      "fetch",
      fetchMock,
    );

    const result =
      await askQuestion(
        "tenant-1",
        "What is this?",
        "conversation-1",
      );

    expect(
      result.answer,
    ).toBe(
      "This is KnowledgeHub.",
    );

    expect(
      fetchMock,
    ).toHaveBeenCalledWith(
      "/rag/tenant-1/ask",
      expect.objectContaining({
        method: "POST",
        headers:
          expect.any(Headers),
      }),
    );

    const call =
      fetchMock.mock.calls[0];

    const options = call[1];

    expect(
      options.headers.get(
        "Authorization",
      ),
    ).toBe(
      `Bearer ${token}`,
    );

    expect(
      JSON.parse(options.body),
    ).toEqual({
      question: "What is this?",
      top_k: 5,
      conversation_id:
        "conversation-1",
    });
  });

  it("clears the session", () => {
    sessionStorage.setItem(
      "knowledgehub_session",
      JSON.stringify({
        accessToken: "token",
      }),
    );

    clearSession();

    expect(
      getSession(),
    ).toBeNull();
  });
});

function createTestJwt(
  payload,
) {
  const encode = (value) =>
    btoa(
      JSON.stringify(value),
    )
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");

  return [
    encode({
      alg: "HS256",
      typ: "JWT",
    }),
    encode(payload),
    "signature",
  ].join(".");
}