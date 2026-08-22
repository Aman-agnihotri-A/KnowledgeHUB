import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";

import App from "./App";

import {
  askQuestion,
  clearSession,
  createConversation,
  createTenant,
  createTenantUser,
  downloadDocument,
  getConversation,
  getSession,
  listConversations,
  listDocuments,
  listTenantUsers,
  listTenants,
  login,
  processDocument,
  updateTenantUserStatus,
  uploadDocument,
} from "./api";

vi.mock("./api", () => ({
  askQuestion: vi.fn(),
  clearSession: vi.fn(),
  createConversation: vi.fn(),
  createTenantUser: vi.fn(),
  downloadDocument: vi.fn(),
  getConversation: vi.fn(),
  getSession: vi.fn(),
  listConversations: vi.fn(),
  listDocuments: vi.fn(),
  listTenantUsers: vi.fn(),
  listTenants: vi.fn(),
  login: vi.fn(),
  processDocument: vi.fn(),
  updateTenantUserStatus: vi.fn(),
  uploadDocument: vi.fn(),
}));

const tenantAdminSession = {
  accessToken: "tenant-admin-token",
  tokenType: "bearer",
  userId: "tenant-admin-1",
  role: "tenant_admin",
  tenantId: "tenant-1",
};

const subUserSession = {
  accessToken: "sub-user-token",
  tokenType: "bearer",
  userId: "sub-user-1",
  role: "sub_user",
  tenantId: "tenant-1",
};

const superAdminSession = {
  accessToken: "super-admin-token",
  tokenType: "bearer",
  userId: "super-admin-1",
  role: "super_admin",
  tenantId: null,
};

const documentFixture = {
  id: "document-1",
  tenant_id: "tenant-1",
  filename: "KnowledgeHub_Guide.pdf",
  status: "ready",
};

const conversationFixture = {
  id: "conversation-1",
  tenant_id: "tenant-1",
  user_id: "tenant-admin-1",
  title: "KnowledgeHub Guide",
  updated_at: "2026-08-22T10:00:00Z",
};

const conversationWithMessages = {
  ...conversationFixture,
  messages: [
    {
      id: "message-1",
      role: "user",
      content: "What is KnowledgeHub?",
      created_at: "2026-08-22T10:00:00Z",
      sources: [],
    },
    {
      id: "message-2",
      role: "assistant",
      content:
        "KnowledgeHub is a tenant-isolated knowledge platform.",
      created_at: "2026-08-22T10:00:01Z",
      sources: [
        {
          chunk_id: "chunk-1",
          document_id: "document-1",
          document_filename:
            "KnowledgeHub_Guide.pdf",
          chunk_index: 0,
          similarity: 0.932,
        },
      ],
    },
  ],
};

describe("KnowledgeHub frontend workflows", () => {
  beforeEach(() => {
    sessionStorage.clear();

    vi.clearAllMocks();

    getSession.mockReturnValue(null);

    listConversations.mockResolvedValue([]);
    listDocuments.mockResolvedValue([]);
    listTenantUsers.mockResolvedValue([]);
    listTenants.mockResolvedValue([]);

    createConversation.mockResolvedValue(
      conversationFixture,
    );

    getConversation.mockResolvedValue(
      conversationWithMessages,
    );

    askQuestion.mockResolvedValue({
      question: "What is KnowledgeHub?",
      answer:
        "KnowledgeHub is a tenant-isolated knowledge platform.",
      abstained: false,
      conversation_id:
        "conversation-1",
      sources: [
        {
          chunk_id: "chunk-1",
          document_id: "document-1",
          document_filename:
            "KnowledgeHub_Guide.pdf",
          chunk_index: 0,
          similarity: 0.932,
        },
      ],
    });

    createTenantUser.mockResolvedValue({
      id: "user-2",
      email: "user2@example.com",
      full_name: "Demo User",
      role: "sub_user",
      tenant_id: "tenant-1",
      is_active: true,
    });

    updateTenantUserStatus.mockResolvedValue({
      id: "user-2",
      email: "user2@example.com",
      full_name: "Demo User",
      role: "sub_user",
      tenant_id: "tenant-1",
      is_active: false,
    });

    listTenants.mockResolvedValue([
      {
        id: "tenant-1",
        name: "Acme Corporation",
        slug: "acme",
        is_active: true,
      },
    ]);

    listTenantUsers.mockResolvedValue([
      {
        id: "user-2",
        email: "user2@example.com",
        full_name: "Demo User",
        role: "sub_user",
        tenant_id: "tenant-1",
        is_active: true,
      },
    ]);

    listDocuments.mockResolvedValue([
      documentFixture,
    ]);

    uploadDocument.mockResolvedValue({
      id: "document-2",
      tenant_id: "tenant-1",
      filename: "NewGuide.pdf",
      status: "uploaded",
    });

    processDocument.mockResolvedValue({
      id: "document-2",
      tenant_id: "tenant-1",
      filename: "NewGuide.pdf",
      status: "ready",
    });

    downloadDocument.mockResolvedValue(
      undefined,
    );

    login.mockResolvedValue(
      tenantAdminSession,
    );

    clearSession.mockImplementation(() => {
      sessionStorage.removeItem(
        "knowledgehub_session",
      );
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the login page when no session exists", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", {
        name: "KnowledgeHub",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByLabelText("Email"),
    ).toBeInTheDocument();

    expect(
      screen.getByLabelText("Password"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", {
        name: "Sign in",
      }),
    ).toBeInTheDocument();
  });

  it("logs in and opens the Tenant Admin workspace", async () => {
    render(<App />);

    fireEvent.change(
      screen.getByLabelText("Email"),
      {
        target: {
          value:
            "admin@knowledgehub.local",
        },
      },
    );

    fireEvent.change(
      screen.getByLabelText("Password"),
      {
        target: {
          value: "Admin@123",
        },
      },
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Sign in",
      }),
    );

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith(
        "admin@knowledgehub.local",
        "Admin@123",
      );
    });

    expect(
      await screen.findByRole(
        "heading",
        {
          name: "Documents",
        },
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Tenant Users",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Knowledge Assistant",
      }),
    ).toBeInTheDocument();
  });

  it("loads the Tenant Admin document and user workspace", async () => {
    getSession.mockReturnValue(
      tenantAdminSession,
    );

    render(<App />);

    expect(
      await screen.findByText(
        "KnowledgeHub_Guide.pdf",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Demo User"),
    ).toBeInTheDocument();

    expect(
      listDocuments,
    ).toHaveBeenCalledWith(
      "tenant-1",
      null,
    );

    expect(
      listTenantUsers,
    ).toHaveBeenCalledWith(
      "tenant-1",
    );

    expect(
      listConversations,
    ).toHaveBeenCalledWith(
      "tenant-1",
    );
  });

  it("allows a Tenant Admin to filter documents", async () => {
    getSession.mockReturnValue(
      tenantAdminSession,
    );

    listDocuments
      .mockResolvedValueOnce([
        {
          ...documentFixture,
          status: "ready",
        },
      ])
      .mockResolvedValueOnce([
        {
          ...documentFixture,
          status: "failed",
        },
      ]);

    render(<App />);

    await screen.findByText(
      "KnowledgeHub_Guide.pdf",
    );

    const statusSelect =
      screen.getByLabelText("Status");

    fireEvent.change(
      statusSelect,
      {
        target: {
          value: "failed",
        },
      },
    );

    await waitFor(() => {
      expect(
        listDocuments,
      ).toHaveBeenLastCalledWith(
        "tenant-1",
        "failed",
      );
    });
  });

  it("shows document processing controls only to Tenant Admins", async () => {
    getSession.mockReturnValue(
      tenantAdminSession,
    );

    listDocuments.mockResolvedValue([
      {
        ...documentFixture,
        status: "uploaded",
      },
    ]);

    render(<App />);

    await screen.findByText(
      "KnowledgeHub_Guide.pdf",
    );

    expect(
      screen.getByRole("button", {
        name: "Process",
      }),
    ).toBeInTheDocument();
  });

  it("does not show document processing controls to Sub Users", async () => {
    getSession.mockReturnValue(
      subUserSession,
    );

    listDocuments.mockResolvedValue([
      documentFixture,
    ]);

    render(<App />);

    await screen.findByText(
      "KnowledgeHub_Guide.pdf",
    );

    expect(
      screen.queryByRole("button", {
        name: "Process",
      }),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByRole("heading", {
        name: "Tenant Users",
      }),
    ).not.toBeInTheDocument();
  });

  it("allows a Tenant Admin to download a document", async () => {
    getSession.mockReturnValue(
      tenantAdminSession,
    );

    listDocuments.mockResolvedValue([
      documentFixture,
    ]);

    render(<App />);

    await screen.findByText(
      "KnowledgeHub_Guide.pdf",
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Download",
      }),
    );

    await waitFor(() => {
      expect(
        downloadDocument,
      ).toHaveBeenCalledWith(
        "tenant-1",
        "document-1",
      );
    });
  });

  it("allows a Tenant Admin to create a Sub User", async () => {
    getSession.mockReturnValue(
      tenantAdminSession,
    );

    render(<App />);

    await screen.findByRole("heading", {
      name: "Tenant Users",
    });

    fireEvent.change(
      screen.getByLabelText(
        "Full name",
      ),
      {
        target: {
          value: "New Sub User",
        },
      },
    );

    const emailInputs =
    screen.getAllByLabelText("Email");

    fireEvent.change(
    emailInputs[emailInputs.length - 1],
    {
        target: {
        value:
            "newuser@example.com",
        },
    },
    );

    fireEvent.change(
      screen.getByLabelText(
        "Temporary password",
      ),
      {
        target: {
          value: "Password@123",
        },
      },
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Create Sub User",
      }),
    );

    await waitFor(() => {
      expect(
        createTenantUser,
      ).toHaveBeenCalledWith(
        "tenant-1",
        {
          full_name: "New Sub User",
          email:
            "newuser@example.com",
          password: "Password@123",
          role: "sub_user",
        },
      );
    });

    expect(
      await screen.findByText(
        "New Sub User",
      ),
    ).toBeInTheDocument();
  });

  it("renders the Super Admin tenant workspace", async () => {
    getSession.mockReturnValue(
      superAdminSession,
    );

    render(<App />);

    expect(
      await screen.findByRole(
        "heading",
        {
          name: "Tenant Management",
        },
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Acme Corporation",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Create Tenant",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Demo User",
      }),
    ).not.toBeInTheDocument();

    expect(
      listTenants,
    ).toHaveBeenCalledTimes(1);
  });

  it("allows Super Admin to create a tenant", async () => {
    getSession.mockReturnValue(
      superAdminSession,
    );

    createTenantUser.mockResolvedValue({
      id: "tenant-admin-2",
      email:
        "admin2@example.com",
      full_name: "Tenant Admin 2",
      role: "tenant_admin",
      tenant_id: "tenant-2",
      is_active: true,
    });

    render(<App />);

    await screen.findByRole("heading", {
      name: "Tenant Management",
    });

    fireEvent.change(
      screen.getByLabelText(
        "Tenant name",
      ),
      {
        target: {
          value: "New Corporation",
        },
      },
    );

    fireEvent.change(
      screen.getByLabelText(
        "Tenant slug",
      ),
      {
        target: {
          value: "new-corporation",
        },
      },
    );

    createConversation.mockClear();

    const tenant =
      {
        id: "tenant-2",
        name: "New Corporation",
        slug: "new-corporation",
        is_active: true,
      };

    vi.mocked(
      listTenants,
    ).mockResolvedValueOnce([
      {
        id: "tenant-1",
        name: "Acme Corporation",
        slug: "acme",
        is_active: true,
      },
    ]);


    createTenant.mockResolvedValueOnce(
      tenant,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Create Tenant",
      }),
    );

    await waitFor(() => {
      expect(
        createTenant,
      ).toHaveBeenCalledWith({
        name: "New Corporation",
        slug: "new-corporation",
      });
    });

    expect(
      await screen.findByText(
        "New Corporation",
      ),
    ).toBeInTheDocument();
  });

  it("loads an existing conversation and renders its sources", async () => {
    getSession.mockReturnValue(
      tenantAdminSession,
    );

    listConversations.mockResolvedValue([
      conversationFixture,
    ]);

    getConversation.mockResolvedValue(
      conversationWithMessages,
    );

    render(<App />);

    expect(
      await screen.findByText(
        "KnowledgeHub is a tenant-isolated knowledge platform.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "KnowledgeHub_Guide.pdf",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Chunk 0",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Similarity 0.932",
      ),
    ).toBeInTheDocument();
  });

  it("creates a conversation and asks a RAG question", async () => {
    getSession.mockReturnValue(
      subUserSession,
    );

    listConversations.mockResolvedValue(
      [],
    );

    const newConversation = {
      ...conversationFixture,
      title: "What is KnowledgeHub?",
    };

    createConversation.mockResolvedValue(
      newConversation,
    );

    getConversation.mockResolvedValue({
      ...newConversation,
      messages: [
        {
          id: "message-user",
          role: "user",
          content:
            "What is KnowledgeHub?",
          sources: [],
        },
        {
          id: "message-assistant",
          role: "assistant",
          content:
            "KnowledgeHub is a tenant-isolated knowledge platform.",
          sources: [],
        },
      ],
    });

    render(<App />);

    await screen.findByRole("heading", {
      name: "Knowledge Assistant",
    });

    const composer =
      screen.getByPlaceholderText(
        "Ask a question about your knowledge base...",
      );

    fireEvent.change(
      composer,
      {
        target: {
          value:
            "What is KnowledgeHub?",
        },
      },
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Ask",
      }),
    );

    await waitFor(() => {
      expect(
        createConversation,
      ).toHaveBeenCalledWith(
        "tenant-1",
        "What is KnowledgeHub?",
      );
    });

    await waitFor(() => {
      expect(
        askQuestion,
      ).toHaveBeenCalledWith(
        "tenant-1",
        "What is KnowledgeHub?",
        "conversation-1",
      );
    });

    expect(
      await screen.findByText(
        "KnowledgeHub is a tenant-isolated knowledge platform.",
      ),
    ).toBeInTheDocument();
  });

  it("logs out and returns to the login page", async () => {
    getSession.mockReturnValue(
      tenantAdminSession,
    );

    render(<App />);

    await screen.findByRole("heading", {
      name: "Documents",
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Sign out",
      }),
    );

    expect(
      clearSession,
    ).toHaveBeenCalledTimes(1);

    expect(
      screen.getByRole("button", {
        name: "Sign in",
      }),
    ).toBeInTheDocument();
  });
});