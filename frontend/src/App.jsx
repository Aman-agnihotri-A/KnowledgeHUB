import {
  useEffect,
  useState,
} from "react";

import {
  askQuestion,
  clearSession,
  createConversation,
  getConversation,
  getSession,
  listConversations,
  listDocuments,
  login,
  processDocument,
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

  const [selectedFile, setSelectedFile] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [uploading, setUploading] =
    useState(false);

  const [processingId, setProcessingId] =
    useState(null);

  const [error, setError] =
    useState("");

  async function loadDocuments() {
    setLoading(true);
    setError("");

    try {
      const result =
        await listDocuments(
          session.tenantId,
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
    loadDocuments();
  }, [session.tenantId]);

  async function handleUpload(
    event,
  ) {
    event.preventDefault();

    if (!selectedFile || uploading) {
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
      const document =
        await uploadDocument(
          session.tenantId,
          selectedFile,
        );

      setDocuments(
        (current) => [
          document,
          ...current,
        ],
      );

      setSelectedFile(null);

      const fileInput =
        document.querySelector(
          "#document-upload-input",
        );

      if (fileInput) {
        fileInput.value = "";
      }

      await handleProcess(
        document,
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
          current.map((item) =>
            item.id === processed.id
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

  return (
    <section className="documents-panel">
      <div className="documents-header">
        <div>
          <h2>Documents</h2>

          <p className="muted">
            Documents available to
            your tenant.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadDocuments}
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
        ) : documents.length === 0 ? (
          <p className="document-empty">
            No documents have been
            uploaded yet.
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
                    {document.filename}
                  </strong>

                  <span>
                    Status:{" "}
                    {document.status}
                  </span>
                </div>

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
              </article>
            ),
          )
        )}
      </div>
    </section>
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

  const isSuperAdmin =
    session.role ===
    "super_admin";

  if (isSuperAdmin) {
    return (
      <div className="unsupported-page">
        <h1>KnowledgeHub</h1>

        <p>
          Chat is currently
          available to tenant users.
        </p>

        <button
          type="button"
          className="primary-button"
          onClick={onLogout}
        >
          Sign out
        </button>
      </div>
    );
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

  return (
    <ChatPage
      session={session}
      onLogout={handleLogout}
    />
  );
}