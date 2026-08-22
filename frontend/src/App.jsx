import {
  useEffect,
  useState,
} from "react";

import {
  askQuestion,
  clearSession,
  createConversation,
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

function LoginPage({
  onLogin,
}) {
  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  async function handleSubmit(
    event,
  ) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const session =
        await login(
          email,
          password,
        );

      onLogin(session);
    } catch (err) {
      setError(
        err.message ||
          "Unable to log in.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="brand-mark">
          KH
        </div>

        <h1>KnowledgeHub</h1>

        <p className="muted">
          Your tenant knowledge
          assistant.
        </p>

        <form
          onSubmit={handleSubmit}
          className="login-form"
        >
          <label>
            Email

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(
                  event.target.value,
                )
              }
              required
              autoComplete="username"
            />
          </label>

          <label>
            Password

            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(
                  event.target.value,
                )
              }
              required
              autoComplete="current-password"
            />
          </label>

          {error && (
            <div className="error-banner">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="primary-button"
          >
            {loading
              ? "Signing in..."
              : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}

function ConversationSidebar({
  conversations,
  selectedConversationId,
  onSelect,
  onNewConversation,
  onLogout,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div>
          <strong>
            KnowledgeHub
          </strong>

          <span className="sidebar-label">
            Conversations
          </span>
        </div>

        <button
          type="button"
          className="icon-button"
          onClick={onNewConversation}
          title="New conversation"
        >
          +
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length ===
          0 && (
          <p className="empty-sidebar">
            No conversations yet.
          </p>
        )}

        {conversations.map(
          (conversation) => (
            <button
              type="button"
              key={conversation.id}
              className={
                conversation.id ===
                selectedConversationId
                  ? "conversation-item active"
                  : "conversation-item"
              }
              onClick={() =>
                onSelect(
                  conversation.id,
                )
              }
            >
              <span className="conversation-title">
                {conversation.title ||
                  "Untitled conversation"}
              </span>

              <span className="conversation-date">
                {formatDate(
                  conversation.updated_at,
                )}
              </span>
            </button>
          ),
        )}
      </div>

      <div className="sidebar-footer">
        <button
          type="button"
          className="logout-button"
          onClick={onLogout}
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}

function MessageBubble({
  message,
}) {
  const isUser =
    message.role === "user";

  return (
    <article
      className={
        isUser
          ? "message user-message"
          : "message assistant-message"
      }
    >
      <div className="message-role">
        {isUser
          ? "You"
          : "KnowledgeHub"}
      </div>

      <div className="message-content">
        {message.content}
      </div>

      {!isUser &&
        message.sources?.length >
          0 && (
          <div className="sources">
            <div className="sources-title">
              Sources
            </div>

            {message.sources.map(
              (source, index) => (
                <div
                  key={
                    source.chunk_id ||
                    index
                  }
                  className="source-card"
                >
                  <strong>
                    {source.document_filename}
                  </strong>

                  <span>
                    Chunk{" "}
                    {source.chunk_index}
                  </span>

                  {typeof source.similarity ===
                    "number" && (
                    <span>
                      Similarity{" "}
                      {source.similarity.toFixed(
                        3,
                      )}
                    </span>
                  )}
                </div>
              ),
            )}
          </div>
        )}
    </article>
  );
}

function DocumentManager({
  session,
}) {
  const [documents, setDocuments] =
    useState([]);

  const [
    selectedFile,
    setSelectedFile,
  ] = useState(null);

  const [
    statusFilter,
    setStatusFilter,
  ] = useState("");

  const [loading, setLoading] =
    useState(true);

  const [uploading, setUploading] =
    useState(false);

  const [processingId, setProcessingId] =
    useState(null);

  const [downloadingId, setDownloadingId] =
    useState(null);

  const [error, setError] =
    useState("");

  async function loadDocuments(
    filter = statusFilter,
  ) {
    setLoading(true);
    setError("");

    try {
      const result =
        await listDocuments(
          session.tenantId,
          filter || null,
        );

      setDocuments(result);
    } catch (err) {
      setError(
        err.message ||
          "Unable to load documents.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments(statusFilter);
  }, [
    session.tenantId,
    statusFilter,
  ]);

  async function handleUpload(
    event,
  ) {
    event.preventDefault();

    if (
      !selectedFile ||
      uploading
    ) {
      return;
    }

    if (
      selectedFile.type !==
        "application/pdf" &&
      !selectedFile.name
        .toLowerCase()
        .endsWith(".pdf")
    ) {
      setError(
        "Only PDF documents are supported.",
      );

      return;
    }

    setUploading(true);
    setError("");

    try {
      const uploadedDocument =
        await uploadDocument(
          session.tenantId,
          selectedFile,
        );

      setDocuments(
        (current) => [
          uploadedDocument,
          ...current,
        ],
      );

      setSelectedFile(null);

      const fileInput =
        window.document.querySelector(
          "#document-upload-input",
        );

      if (fileInput) {
        fileInput.value = "";
      }

      await handleProcess(
        uploadedDocument,
      );
    } catch (err) {
      setError(
        err.message ||
          "Unable to upload document.",
      );
    } finally {
      setUploading(false);
    }
  }

  async function handleProcess(
    document,
  ) {
    setProcessingId(
      document.id,
    );

    setError("");

    try {
      const processed =
        await processDocument(
          session.tenantId,
          document.id,
        );

      setDocuments(
        (current) =>
          current.map(
            (item) =>
              item.id ===
              processed.id
                ? processed
                : item,
          ),
      );
    } catch (err) {
      setError(
        err.message ||
          "Unable to process document.",
      );

      await loadDocuments();
    } finally {
      setProcessingId(null);
    }
  }

  async function handleDownload(
    document,
  ) {
    setDownloadingId(
      document.id,
    );

    setError("");

    try {
      await downloadDocument(
        session.tenantId,
        document.id,
      );
    } catch (err) {
      setError(
        err.message ||
          "Unable to download document.",
      );
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <section className="documents-panel">
      <div className="documents-header">
        <div>
          <h2>
            Documents
          </h2>

          <p className="muted">
            Documents available to
            your tenant.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() =>
            loadDocuments()
          }
          disabled={loading}
        >
          Refresh
        </button>
      </div>

      {session.role ===
        "tenant_admin" && (
        <form
          className="upload-form"
          onSubmit={handleUpload}
        >
          <label
            className="upload-label"
            htmlFor="document-upload-input"
          >
            Upload PDF
          </label>

          <div className="upload-controls">
            <input
              id="document-upload-input"
              type="file"
              accept=".pdf,application/pdf"
              onChange={(event) =>
                setSelectedFile(
                  event.target.files?.[0] ||
                    null,
                )
              }
              disabled={uploading}
            />

            <button
              type="submit"
              className="primary-button"
              disabled={
                uploading ||
                !selectedFile
              }
            >
              {uploading
                ? "Uploading..."
                : "Upload"}
            </button>
          </div>
        </form>
      )}

      <div className="document-toolbar">
        <label>
          Status

          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(
                event.target.value,
              )
            }
            disabled={loading}
          >
            <option value="">
              All statuses
            </option>

            <option value="uploaded">
              Uploaded
            </option>

            <option value="processing">
              Processing
            </option>

            <option value="ready">
              Ready
            </option>

            <option value="failed">
              Failed
            </option>
          </select>
        </label>
      </div>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      <div className="document-list">
        {loading ? (
          <p className="document-empty">
            Loading documents...
          </p>
        ) : documents.length ===
          0 ? (
          <p className="document-empty">
            No documents found for
            this filter.
          </p>
        ) : (
          documents.map(
            (document) => (
              <article
                key={document.id}
                className="document-card"
              >
                <div className="document-info">
                  <strong>
                    {
                      document.filename
                    }
                  </strong>

                  <span>
                    Status:{" "}
                    {
                      document.status
                    }
                  </span>
                </div>

                <div className="document-actions">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      handleDownload(
                        document,
                      )
                    }
                    disabled={
                      downloadingId ===
                      document.id
                    }
                  >
                    {downloadingId ===
                    document.id
                      ? "Downloading..."
                      : "Download"}
                  </button>

                  {session.role ===
                    "tenant_admin" &&
                    document.status !==
                      "ready" && (
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() =>
                          handleProcess(
                            document,
                          )
                        }
                        disabled={
                          processingId ===
                          document.id
                        }
                      >
                        {processingId ===
                        document.id
                          ? "Processing..."
                          : "Process"}
                      </button>
                    )}
                </div>
              </article>
            ),
          )
        )}
      </div>
    </section>
  );
}

function UserManager({
  session,
}) {
  const [users, setUsers] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [submitting, setSubmitting] =
    useState(false);

  const [updatingId, setUpdatingId] =
    useState(null);

  const [error, setError] =
    useState("");

  const [form, setForm] =
    useState({
      full_name: "",
      email: "",
      password: "",
    });

  async function loadUsers() {
    setLoading(true);
    setError("");

    try {
      const result =
        await listTenantUsers(
          session.tenantId,
        );

      setUsers(result);
    } catch (err) {
      setError(
        err.message ||
          "Unable to load users.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
  }, [session.tenantId]);

  function handleChange(event) {
    const {
      name,
      value,
    } = event.target;

    setForm(
      (current) => ({
        ...current,
        [name]: value,
      }),
    );
  }

  async function handleCreate(
    event,
  ) {
    event.preventDefault();

    if (submitting) {
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const user =
        await createTenantUser(
          session.tenantId,
          {
            full_name:
              form.full_name.trim(),
            email:
              form.email.trim(),
            password:
              form.password,
            role: "sub_user",
          },
        );

      setUsers(
        (current) => [
          user,
          ...current,
        ],
      );

      setForm({
        full_name: "",
        email: "",
        password: "",
      });
    } catch (err) {
      setError(
        err.message ||
          "Unable to create user.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleStatusChange(
    user,
  ) {
    if (updatingId) {
      return;
    }

    setUpdatingId(user.id);
    setError("");

    try {
      const updated =
        await updateTenantUserStatus(
          session.tenantId,
          user.id,
          !user.is_active,
        );

      setUsers(
        (current) =>
          current.map((item) =>
            item.id === updated.id
              ? updated
              : item,
          ),
      );
    } catch (err) {
      setError(
        err.message ||
          "Unable to update user.",
      );
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <section className="users-panel">
      <div className="users-header">
        <div>
          <h2>
            Tenant Users
          </h2>

          <p className="muted">
            Manage Sub Users in
            your tenant.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadUsers}
          disabled={loading}
        >
          Refresh
        </button>
      </div>

      <form
        className="user-create-form"
        onSubmit={handleCreate}
      >
        <div className="user-form-grid">
          <label>
            Full name

            <input
              name="full_name"
              type="text"
              value={
                form.full_name
              }
              onChange={
                handleChange
              }
              required
            />
          </label>

          <label>
            Email

            <input
              name="email"
              type="email"
              value={form.email}
              onChange={
                handleChange
              }
              required
            />
          </label>

          <label>
            Temporary password

            <input
              name="password"
              type="password"
              value={
                form.password
              }
              onChange={
                handleChange
              }
              required
              minLength={8}
            />
          </label>
        </div>

        <button
          type="submit"
          className="primary-button"
          disabled={submitting}
        >
          {submitting
            ? "Creating..."
            : "Create Sub User"}
        </button>
      </form>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      <div className="user-list">
        {loading ? (
          <p className="document-empty">
            Loading users...
          </p>
        ) : users.length === 0 ? (
          <p className="document-empty">
            No Sub Users yet.
          </p>
        ) : (
          users.map((user) => (
            <article
              key={user.id}
              className="user-card"
            >
              <div className="user-info">
                <strong>
                  {user.full_name}
                </strong>

                <span>
                  {user.email}
                </span>

                <span>
                  {user.role}
                </span>
              </div>

              <div className="user-actions">
                <span
                  className={
                    user.is_active
                      ? "status-active"
                      : "status-inactive"
                  }
                >
                  {user.is_active
                    ? "ACTIVE"
                    : "INACTIVE"}
                </span>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() =>
                    handleStatusChange(
                      user,
                    )
                  }
                  disabled={
                    updatingId ===
                    user.id
                  }
                >
                  {updatingId ===
                  user.id
                    ? "Updating..."
                    : user.is_active
                      ? "Deactivate"
                      : "Activate"}
                </button>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}

function SuperAdminPage({
  session,
  onLogout,
}) {
  const [tenants, setTenants] =
    useState([]);

  const [
    selectedTenantId,
    setSelectedTenantId,
  ] = useState(null);

  const [users, setUsers] =
    useState([]);

  const [loadingTenants, setLoadingTenants] =
    useState(true);

  const [loadingUsers, setLoadingUsers] =
    useState(false);

  const [creatingTenant, setCreatingTenant] =
    useState(false);

  const [creatingUser, setCreatingUser] =
    useState(false);

  const [updatingUserId, setUpdatingUserId] =
    useState(null);

  const [error, setError] =
    useState("");

  const [tenantForm, setTenantForm] =
    useState({
      name: "",
      slug: "",
    });

  const [userForm, setUserForm] =
    useState({
      full_name: "",
      email: "",
      password: "",
      role: "tenant_admin",
    });

  async function loadTenants() {
    setLoadingTenants(true);
    setError("");

    try {
      const result =
        await listTenants();

      setTenants(result);

      if (
        result.length > 0 &&
        !selectedTenantId
      ) {
        setSelectedTenantId(
          result[0].id,
        );
      }
    } catch (err) {
      setError(
        err.message ||
          "Unable to load tenants.",
      );
    } finally {
      setLoadingTenants(false);
    }
  }

  async function loadUsers(
    tenantId,
  ) {
    if (!tenantId) {
      setUsers([]);
      return;
    }

    setLoadingUsers(true);
    setError("");

    try {
      const result =
        await listTenantUsers(
          tenantId,
        );

      setUsers(result);
    } catch (err) {
      setError(
        err.message ||
          "Unable to load tenant users.",
      );
    } finally {
      setLoadingUsers(false);
    }
  }

  useEffect(() => {
    loadTenants();
  }, []);

  useEffect(() => {
    loadUsers(
      selectedTenantId,
    );
  }, [selectedTenantId]);

  function handleTenantChange(
    event,
  ) {
    const {
      name,
      value,
    } = event.target;

    setTenantForm(
      (current) => ({
        ...current,
        [name]: value,
      }),
    );
  }

  function handleUserChange(
    event,
  ) {
    const {
      name,
      value,
    } = event.target;

    setUserForm(
      (current) => ({
        ...current,
        [name]: value,
      }),
    );
  }

  async function handleCreateTenant(
    event,
  ) {
    event.preventDefault();

    if (creatingTenant) {
      return;
    }

    setCreatingTenant(true);
    setError("");

    try {
      const tenant =
        await createTenant({
          name:
            tenantForm.name.trim(),
          slug:
            tenantForm.slug.trim(),
        });

      setTenants(
        (current) => [
          tenant,
          ...current,
        ],
      );

      setSelectedTenantId(
        tenant.id,
      );

      setTenantForm({
        name: "",
        slug: "",
      });
    } catch (err) {
      setError(
        err.message ||
          "Unable to create tenant.",
      );
    } finally {
      setCreatingTenant(false);
    }
  }

  async function handleCreateUser(
    event,
  ) {
    event.preventDefault();

    if (
      creatingUser ||
      !selectedTenantId
    ) {
      return;
    }

    setCreatingUser(true);
    setError("");

    try {
      const user =
        await createTenantUser(
          selectedTenantId,
          {
            full_name:
              userForm.full_name.trim(),
            email:
              userForm.email.trim(),
            password:
              userForm.password,
            role:
              userForm.role,
          },
        );

      setUsers(
        (current) => [
          user,
          ...current,
        ],
      );

      setUserForm({
        full_name: "",
        email: "",
        password: "",
        role: "tenant_admin",
      });
    } catch (err) {
      setError(
        err.message ||
          "Unable to create user.",
      );
    } finally {
      setCreatingUser(false);
    }
  }

  async function handleStatusChange(
    user,
  ) {
    if (
      updatingUserId ||
      !selectedTenantId
    ) {
      return;
    }

    setUpdatingUserId(
      user.id,
    );
    setError("");

    try {
      const updated =
        await updateTenantUserStatus(
          selectedTenantId,
          user.id,
          !user.is_active,
        );

      setUsers(
        (current) =>
          current.map(
            (item) =>
              item.id === updated.id
                ? updated
                : item,
          ),
      );
    } catch (err) {
      setError(
        err.message ||
          "Unable to update user.",
      );
    } finally {
      setUpdatingUserId(null);
    }
  }

  const selectedTenant =
    tenants.find(
      (tenant) =>
        tenant.id ===
        selectedTenantId,
    );

  return (
    <main className="admin-page">
      <header className="admin-header">
        <div>
          <strong>
            KnowledgeHub
          </strong>

          <span className="sidebar-label">
            Super Admin
          </span>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={onLogout}
        >
          Sign out
        </button>
      </header>

      <section className="admin-content">
        <div className="admin-title">
          <div>
            <h1>
              Tenant Management
            </h1>

            <p className="muted">
              Create tenants and
              manage their users.
            </p>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={loadTenants}
            disabled={
              loadingTenants
            }
          >
            Refresh
          </button>
        </div>

        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}

        <section className="admin-card">
          <div className="admin-card-header">
            <div>
              <h2>
                Create Tenant
              </h2>

              <p className="muted">
                Add a new tenant to
                KnowledgeHub.
              </p>
            </div>
          </div>

          <form
            className="admin-form"
            onSubmit={
              handleCreateTenant
            }
          >
            <label>
              Tenant name

              <input
                name="name"
                type="text"
                value={
                  tenantForm.name
                }
                onChange={
                  handleTenantChange
                }
                required
              />
            </label>

            <label>
              Tenant slug

              <input
                name="slug"
                type="text"
                value={
                  tenantForm.slug
                }
                onChange={
                  handleTenantChange
                }
                required
              />
            </label>

            <button
              type="submit"
              className="primary-button"
              disabled={
                creatingTenant
              }
            >
              {creatingTenant
                ? "Creating..."
                : "Create Tenant"}
            </button>
          </form>
        </section>

        <section className="admin-card">
          <div className="admin-card-header">
            <div>
              <h2>
                Tenants
              </h2>

              <p className="muted">
                Select a tenant to
                manage its users.
              </p>
            </div>
          </div>

          {loadingTenants ? (
            <p className="document-empty">
              Loading tenants...
            </p>
          ) : tenants.length === 0 ? (
            <p className="document-empty">
              No tenants yet.
            </p>
          ) : (
            <div className="tenant-list">
              {tenants.map(
                (tenant) => (
                  <button
                    type="button"
                    key={tenant.id}
                    className={
                      tenant.id ===
                      selectedTenantId
                        ? "tenant-card selected"
                        : "tenant-card"
                    }
                    onClick={() =>
                      setSelectedTenantId(
                        tenant.id,
                      )
                    }
                  >
                    <span>
                      <strong>
                        {tenant.name}
                      </strong>

                      <small>
                        {tenant.slug}
                      </small>
                    </span>

                    <span
                      className={
                        tenant.is_active
                          ? "status-active"
                          : "status-inactive"
                      }
                    >
                      {tenant.is_active
                        ? "ACTIVE"
                        : "INACTIVE"}
                    </span>
                  </button>
                ),
              )}
            </div>
          )}
        </section>

        {selectedTenant && (
          <section className="admin-card">
            <div className="admin-card-header">
              <div>
                <h2>
                  {selectedTenant.name}
                </h2>

                <p className="muted">
                  Manage users for{" "}
                  {selectedTenant.slug}.
                </p>
              </div>
            </div>

            <form
              className="admin-form"
              onSubmit={
                handleCreateUser
              }
            >
              <label>
                Full name

                <input
                  name="full_name"
                  type="text"
                  value={
                    userForm.full_name
                  }
                  onChange={
                    handleUserChange
                  }
                  required
                />
              </label>

              <label>
                Email

                <input
                  name="email"
                  type="email"
                  value={
                    userForm.email
                  }
                  onChange={
                    handleUserChange
                  }
                  required
                />
              </label>

              <label>
                Temporary password

                <input
                  name="password"
                  type="password"
                  value={
                    userForm.password
                  }
                  onChange={
                    handleUserChange
                  }
                  minLength={8}
                  required
                />
              </label>

              <label>
                Role

                <select
                  name="role"
                  value={
                    userForm.role
                  }
                  onChange={
                    handleUserChange
                  }
                >
                  <option value="tenant_admin">
                    Tenant Admin
                  </option>

                  <option value="sub_user">
                    Sub User
                  </option>
                </select>
              </label>

              <button
                type="submit"
                className="primary-button"
                disabled={
                  creatingUser
                }
              >
                {creatingUser
                  ? "Creating..."
                  : "Create User"}
              </button>
            </form>

            <div className="user-list">
              {loadingUsers ? (
                <p className="document-empty">
                  Loading users...
                </p>
              ) : users.length ===
                0 ? (
                <p className="document-empty">
                  No users yet.
                </p>
              ) : (
                users.map(
                  (user) => (
                    <article
                      key={user.id}
                      className="user-card"
                    >
                      <div className="user-info">
                        <strong>
                          {
                            user.full_name
                          }
                        </strong>

                        <span>
                          {user.email}
                        </span>

                        <span>
                          {user.role}
                        </span>
                      </div>

                      <div className="user-actions">
                        <span
                          className={
                            user.is_active
                              ? "status-active"
                              : "status-inactive"
                          }
                        >
                          {user.is_active
                            ? "ACTIVE"
                            : "INACTIVE"}
                        </span>

                        <button
                          type="button"
                          className="secondary-button"
                          onClick={() =>
                            handleStatusChange(
                              user,
                            )
                          }
                          disabled={
                            updatingUserId ===
                            user.id
                          }
                        >
                          {updatingUserId ===
                          user.id
                            ? "Updating..."
                            : user.is_active
                              ? "Deactivate"
                              : "Activate"}
                        </button>
                      </div>
                    </article>
                  ),
                )
              )}
            </div>
          </section>
        )}
      </section>
    </main>
  );
}

function ChatPage({
  session,
  onLogout,
}) {
  const [
    conversations,
    setConversations,
  ] = useState([]);

  const [
    selectedConversationId,
    setSelectedConversationId,
  ] = useState(null);

  const [
    messages,
    setMessages,
  ] = useState([]);

  const [
    question,
    setQuestion,
  ] = useState("");

  const [
    loadingConversations,
    setLoadingConversations,
  ] = useState(true);

  const [
    loadingMessages,
    setLoadingMessages,
  ] = useState(false);

  const [
    sending,
    setSending,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  useEffect(() => {
    loadConversations();
  }, []);

  async function loadConversations() {
    setLoadingConversations(
      true,
    );
    setError("");

    try {
      const result =
        await listConversations(
          session.tenantId,
        );

      setConversations(result);

      if (result.length > 0) {
        await selectConversation(
          result[0].id,
        );
      }
    } catch (err) {
      setError(
        err.message ||
          "Unable to load conversations.",
      );
    } finally {
      setLoadingConversations(
        false,
      );
    }
  }

  async function selectConversation(
    conversationId,
  ) {
    setSelectedConversationId(
      conversationId,
    );

    setLoadingMessages(true);
    setError("");

    try {
      const conversation =
        await getConversation(
          session.tenantId,
          conversationId,
        );

      setMessages(
        conversation.messages ||
          [],
      );
    } catch (err) {
      setError(
        err.message ||
          "Unable to load conversation.",
      );
    } finally {
      setLoadingMessages(false);
    }
  }

  async function handleNewConversation() {
    setError("");

    try {
      const conversation =
        await createConversation(
          session.tenantId,
          "New conversation",
        );

      setConversations(
        (current) => [
          conversation,
          ...current,
        ],
      );

      setSelectedConversationId(
        conversation.id,
      );

      setMessages([]);
    } catch (err) {
      setError(
        err.message ||
          "Unable to create conversation.",
      );
    }
  }

  async function handleSend(
    event,
  ) {
    event.preventDefault();

    const trimmed =
      question.trim();

    if (!trimmed || sending) {
      return;
    }

    setSending(true);
    setError("");

    try {
      let conversationId =
        selectedConversationId;

      if (!conversationId) {
        const title =
          trimmed.length > 60
            ? `${trimmed.slice(
                0,
                57,
              )}...`
            : trimmed;

        const conversation =
          await createConversation(
            session.tenantId,
            title,
          );

        conversationId =
          conversation.id;

        setConversations(
          (current) => [
            conversation,
            ...current,
          ],
        );

        setSelectedConversationId(
          conversationId,
        );
      }

      setQuestion("");

      await askQuestion(
        session.tenantId,
        trimmed,
        conversationId,
      );

      const conversation =
        await getConversation(
          session.tenantId,
          conversationId,
        );

      setMessages(
        conversation.messages ||
          [],
      );

      setConversations(
        (current) =>
          current
            .map((item) =>
              item.id ===
              conversation.id
                ? conversation
                : item,
            )
            .sort(
              (a, b) =>
                new Date(
                  b.updated_at,
                ) -
                new Date(
                  a.updated_at,
                ),
            ),
      );
    } catch (err) {
      setError(
        err.message ||
          "Unable to process your question.",
      );
    } finally {
      setSending(false);
    }
  }


  return (
    <main className="app-shell">
      <ConversationSidebar
        conversations={
          conversations
        }
        selectedConversationId={
          selectedConversationId
        }
        onSelect={
          selectConversation
        }
        onNewConversation={
          handleNewConversation
        }
        onLogout={onLogout}
      />

      <section className="chat-panel">
        <header className="chat-header">
          <div>
            <h1>
              {selectedConversationId
                ? conversations.find(
                    (item) =>
                      item.id ===
                      selectedConversationId,
                  )?.title ||
                  "Conversation"
                : "Knowledge Assistant"}
            </h1>

            <span className="muted">
              Grounded answers from
              your tenant knowledge
              base
            </span>
          </div>

          <span className="role-badge">
            {session.role}
          </span>
        </header>
        <DocumentManager
            session={session}
        />

        {session.role ===
        "tenant_admin" && (
        <UserManager
            session={session}
        />
        )}

        {error && (
          <div className="error-banner page-error">
            {error}
          </div>
        )}

        <div className="messages">
          {loadingConversations ||
          loadingMessages ? (
            <div className="empty-chat">
              Loading...
            </div>
          ) : messages.length ===
            0 ? (
            <div className="empty-chat">
              <div className="empty-icon">
                ?
              </div>

              <h2>
                Ask KnowledgeHub
              </h2>

              <p>
                Ask a question about
                the documents available
                to your tenant.
              </p>
            </div>
          ) : (
            messages.map(
              (message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                />
              ),
            )
          )}

          {sending && (
            <article className="message assistant-message">
              <div className="message-role">
                KnowledgeHub
              </div>

              <div className="thinking">
                Searching the knowledge
                base and generating an
                answer...
              </div>
            </article>
          )}
        </div>

        <form
          className="composer"
          onSubmit={handleSend}
        >
          <textarea
            value={question}
            onChange={(event) =>
              setQuestion(
                event.target.value,
              )
            }
            placeholder="Ask a question about your knowledge base..."
            rows={2}
            disabled={sending}
          />

          <button
            type="submit"
            className="primary-button send-button"
            disabled={
              sending ||
              !question.trim()
            }
          >
            {sending
              ? "Thinking..."
              : "Ask"}
          </button>
        </form>
      </section>
    </main>
  );
}

function formatDate(
  value,
) {
  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      month: "short",
      day: "numeric",
    },
  ).format(new Date(value));
}

export default function App() {
  const [
    session,
    setSession,
  ] = useState(
    () => getSession(),
  );

  function handleLogout() {
    clearSession();
    setSession(null);
  }

  if (!session) {
    return (
      <LoginPage
        onLogin={setSession}
      />
    );
  }

    if (
        session.role ===
        "super_admin"
    ) {
        return (
        <SuperAdminPage
            session={session}
            onLogout={handleLogout}
        />
        );
    }

  return (
    <ChatPage
      session={session}
      onLogout={handleLogout}
    />
  );
}