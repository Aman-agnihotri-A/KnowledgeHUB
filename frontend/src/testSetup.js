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
} from "./api";

describe("frontend API client", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
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