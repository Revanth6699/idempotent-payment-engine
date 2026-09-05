import { useEffect, useMemo, useState } from "react";

import {
  clearTokens,
  createPaymentIntent,
  getAccessToken,
  getMonitoringStatus,
  getRiskAssessment,
  loginUser,
  reconcileTransaction,
  registerUser,
  startTransaction,
} from "./api/api_client";

import "./styles.css";

const HISTORY_KEY = "payment_engine_transaction_history";
const PROFILE_NAME_KEY = "payment_engine_profile_name";

function loadHistory() {
  try {
    return JSON.parse(
      localStorage.getItem(HISTORY_KEY) || "[]",
    );
  } catch {
    return [];
  }
}

function saveHistory(history) {
  localStorage.setItem(
    HISTORY_KEY,
    JSON.stringify(history),
  );
}

/* =========================================================
   ICONS
   ========================================================= */

function Icon({
  name,
  size = 20,
  strokeWidth = 1.8,
}) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": true,
  };

  const paths = {
    dashboard: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),

    payment: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="M3 10h18" />
        <path d="M7 15h4" />
      </>
    ),

    transactions: (
      <>
        <path d="M8 6h13" />
        <path d="M8 12h13" />
        <path d="M8 18h13" />
        <path d="M3 6h.01" />
        <path d="M3 12h.01" />
        <path d="M3 18h.01" />
      </>
    ),

    risk: (
      <>
        <path d="M12 3l8 4v5c0 4.8-3.4 8.2-8 9-4.6-.8-8-4.2-8-9V7l8-4z" />
        <path d="M9 12l2 2 4-4" />
      </>
    ),

    profile: (
      <>
        <circle cx="12" cy="8" r="3.5" />
        <path d="M5 21c.7-3.7 3.1-5.5 7-5.5s6.3 1.8 7 5.5" />
      </>
    ),

    logout: (
      <>
        <path d="M10 17l5-5-5-5" />
        <path d="M15 12H3" />
        <path d="M21 19V5a2 2 0 0 0-2-2h-5" />
      </>
    ),

    arrow: (
      <>
        <path d="M5 12h14" />
        <path d="M13 6l6 6-6 6" />
      </>
    ),

    arrowUp: (
      <>
        <path d="M12 19V5" />
        <path d="M6 11l6-6 6 6" />
      </>
    ),

    arrowDown: (
      <>
        <path d="M12 5v14" />
        <path d="M18 13l-6 6-6-6" />
      </>
    ),

    check: (
      <>
        <path d="M20 6L9 17l-5-5" />
      </>
    ),

    close: (
      <>
        <path d="M6 6l12 12" />
        <path d="M18 6L6 18" />
      </>
    ),

    shield: (
      <>
        <path d="M12 3l8 4v5c0 4.8-3.4 8.2-8 9-4.6-.8-8-4.2-8-9V7l8-4z" />
        <path d="M9 12l2 2 4-4" />
      </>
    ),

    activity: (
      <>
        <path d="M3 12h4l2-6 4 12 2-6h6" />
      </>
    ),

    spark: (
      <>
        <path d="M12 3l1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3z" />
        <path d="M19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16z" />
      </>
    ),

    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),

    refresh: (
      <>
        <path d="M20 11a8 8 0 0 0-14.8-4L3 10" />
        <path d="M3 5v5h5" />
        <path d="M4 13a8 8 0 0 0 14.8 4L21 14" />
        <path d="M21 19v-5h-5" />
      </>
    ),

    chevron: (
      <>
        <path d="M9 18l6-6-6-6" />
      </>
    ),

    menu: (
      <>
        <path d="M4 7h16" />
        <path d="M4 12h16" />
        <path d="M4 17h16" />
      </>
    ),

    plus: (
      <>
        <path d="M12 5v14" />
        <path d="M5 12h14" />
      </>
    ),

    logoutSmall: (
      <>
        <path d="M9 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4" />
        <path d="M14 16l4-4-4-4" />
        <path d="M18 12H9" />
      </>
    ),
  };

  return <svg {...common}>{paths[name]}</svg>;
}

/* =========================================================
   APP
   ========================================================= */

function App() {
  const [authenticated, setAuthenticated] = useState(
    Boolean(getAccessToken()),
  );

  const [view, setView] = useState("dashboard");
  const [history, setHistory] = useState(loadHistory());

  const [selectedTransaction, setSelectedTransaction] =
    useState(null);

  const [risk, setRisk] = useState(null);
  const [monitoring, setMonitoring] = useState(null);

  const [authMode, setAuthMode] = useState("login");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [receiverName, setReceiverName] =
    useState("");

  const [receiverDetails, setReceiverDetails] =
    useState("");

  const [amount, setAmount] = useState("");

  const [displayName, setDisplayName] =
    useState(() =>
      localStorage.getItem(PROFILE_NAME_KEY) || "",
    );

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    saveHistory(history);
  }, [history]);

  useEffect(() => {
    if (authenticated) {
      loadMonitoring();
    }
  }, [authenticated]);

  async function loadMonitoring() {
    try {
      const status = await getMonitoringStatus();
      setMonitoring(status);
    } catch {
      setMonitoring(null);
    }
  }

  function navigate(nextView) {
    setMessage("");
    setError("");
    setView(nextView);
  }

  async function handleAuth(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setMessage("");

    try {
      if (authMode === "register") {
        await registerUser(email, password);

        setMessage(
          "Account created successfully. Sign in to continue.",
        );

        setAuthMode("login");
        setPassword("");
      } else {
        await loginUser(email, password);

        setAuthenticated(true);
        setMessage("Welcome back.");
        setPassword("");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    clearTokens();

    setAuthenticated(false);
    setSelectedTransaction(null);
    setRisk(null);
    setMonitoring(null);
    setView("dashboard");
  }

  function saveProfileName(nextName) {
    const normalizedName = nextName.trim();

    if (!normalizedName) {
      setError("Display name cannot be empty.");
      return false;
    }

    localStorage.setItem(
      PROFILE_NAME_KEY,
      normalizedName,
    );

    setDisplayName(normalizedName);
    setMessage("Profile changes saved.");
    return true;
  }

  async function handlePayment(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const normalizedReceiverName =
        receiverName.trim();
      const normalizedReceiverDetails =
        receiverDetails.trim();
      const numericAmount = Number(amount);

      if (!normalizedReceiverName) {
        throw new Error("Receiver name is required.");
      }

      if (!normalizedReceiverDetails) {
        throw new Error(
          "Receiver details or UPI ID are required.",
        );
      }

      if (
        !Number.isFinite(numericAmount) ||
        numericAmount < 1
      ) {
        throw new Error(
          "Payment amount must be at least INR 1.00.",
        );
      }

      const merchantReference =
        `PAY-${Date.now()}`;

      const idempotencyKey =
        crypto.randomUUID();

      const paymentIntent =
        await createPaymentIntent({
          merchant_reference:
            merchantReference,
          idempotency_key:
            idempotencyKey,
          amount: numericAmount.toFixed(2),
          currency: "INR",
        });

      const transaction =
        await startTransaction(
          paymentIntent.id,
        );

      const record = {
        ...transaction,
        receiver_name:
          normalizedReceiverName,
        receiver_details:
          normalizedReceiverDetails,
        merchant_reference:
          paymentIntent.merchant_reference,
        idempotency_key:
          paymentIntent.idempotency_key,
      };

      setHistory((previous) => {
        const filtered = previous.filter(
          (item) => item.id !== transaction.id,
        );

        return [
          record,
          ...filtered,
        ].slice(0, 50);
      });

      setSelectedTransaction(record);
      setRisk(null);

      setMessage(
        `Payment ${transaction.status.toLowerCase()}.`,
      );

      setView("receipt");

      setReceiverName("");
      setReceiverDetails("");
      setAmount("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadRisk(transaction) {
    setSelectedTransaction(transaction);
    setRisk(null);
    setError("");

    try {
      const result =
        await getRiskAssessment(transaction.id);

      setRisk(result);
    } catch {
      setError(
        "Risk assessment is not available yet. The ML pipeline may still be processing.",
      );
    }

    setView("risk");
  }

  async function handleReconciliation(transaction) {
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const reconciled =
        await reconcileTransaction(
          transaction.id,
        );

      setHistory((previous) =>
        previous.map((item) =>
          item.id === reconciled.id
            ? {
                ...item,
                ...reconciled,
              }
            : item,
        ),
      );

      setSelectedTransaction(reconciled);

      setMessage(
        `Transaction reconciled as ${reconciled.status}.`,
      );

      setView("receipt");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const stats = useMemo(() => {
    return {
      total: history.length,

      successful: history.filter(
        (item) => item.status === "SUCCESS",
      ).length,

      failed: history.filter(
        (item) => item.status === "FAILED",
      ).length,

      unknown: history.filter(
        (item) =>
          item.status === "UNKNOWN" ||
          item.status === "RECONCILING",
      ).length,
    };
  }, [history]);

  if (!authenticated) {
    return (
      <LandingPage
        authMode={authMode}
        setAuthMode={setAuthMode}
        email={email}
        setEmail={setEmail}
        password={password}
        setPassword={setPassword}
        loading={loading}
        message={message}
        error={error}
        onSubmit={handleAuth}
      />
    );
  }

  return (
    <div className="application">
      <Sidebar
        view={view}
        navigate={navigate}
        logout={logout}
        historyCount={history.length}
      />

      <div className="application-main">
        <Topbar
          view={view}
          monitoring={monitoring}
          onProfile={() => navigate("profile")}
          onMenu={() => navigate("dashboard")}
        />

        <main className="content">
          {message && (
            <div className="toast-message toast-success">
              <span className="toast-icon">
                <Icon name="check" size={17} />
              </span>

              <span>{message}</span>

              <button
                type="button"
                onClick={() => setMessage("")}
                aria-label="Dismiss message"
              >
                <Icon name="close" size={16} />
              </button>
            </div>
          )}

          {error && (
            <div className="toast-message toast-error">
              <span className="toast-icon">
                <Icon name="close" size={17} />
              </span>

              <span>{error}</span>

              <button
                type="button"
                onClick={() => setError("")}
                aria-label="Dismiss error"
              >
                <Icon name="close" size={16} />
              </button>
            </div>
          )}

          {view === "dashboard" && (
            <Dashboard
              stats={stats}
              history={history}
              monitoring={monitoring}
              onTransaction={(transaction) => {
                setSelectedTransaction(transaction);
                setView("receipt");
              }}
              onNewPayment={() => navigate("payment")}
              onTransactions={() =>
                navigate("history")
              }
              onRisk={() => navigate("risk")}
            />
          )}

          {view === "payment" && (
            <PaymentPage
              receiverName={receiverName}
              setReceiverName={setReceiverName}
              receiverDetails={receiverDetails}
              setReceiverDetails={
                setReceiverDetails
              }
              amount={amount}
              setAmount={setAmount}
              loading={loading}
              onSubmit={handlePayment}
              onCancel={() => navigate("dashboard")}
            />
          )}

          {view === "history" && (
            <TransactionHistory
              history={history}
              onReceipt={(transaction) => {
                setSelectedTransaction(
                  transaction,
                );
                setView("receipt");
              }}
              onRisk={loadRisk}
              onReconcile={handleReconciliation}
            />
          )}

          {view === "receipt" &&
            selectedTransaction && (
              <Receipt
                transaction={
                  selectedTransaction
                }
                onRisk={loadRisk}
                onReconcile={
                  handleReconciliation
                }
                onBack={() => navigate("history")}
              />
            )}

          {view === "risk" && (
            <RiskDashboard
              transaction={
                selectedTransaction
              }
              risk={risk}
              history={history}
              onLoadRisk={loadRisk}
            />
          )}

          {view === "profile" && (
            <ProfilePage
              email={email}
              displayName={displayName}
              onSave={saveProfileName}
              onBack={() =>
                navigate("dashboard")
              }
            />
          )}
        </main>

        <Footer />
      </div>
    </div>
  );
}

/* =========================================================
   LANDING / AUTH
   ========================================================= */

function LandingPage({
  authMode,
  setAuthMode,
  email,
  setEmail,
  password,
  setPassword,
  loading,
  message,
  error,
  onSubmit,
}) {
  return (
    <div className="landing-shell">
      <div className="landing-orb landing-orb-one" />
      <div className="landing-orb landing-orb-two" />

      <header className="landing-header">
        <Brand />

        <div className="landing-header-actions">
          <button
            type="button"
            className={
              authMode === "login"
                ? "landing-link active"
                : "landing-link"
            }
            onClick={() =>
              setAuthMode("login")
            }
          >
            Sign in
          </button>

          <button
            type="button"
            className="landing-register-button"
            onClick={() =>
              setAuthMode("register")
            }
          >
            Get started
            <Icon name="arrow" size={16} />
          </button>
        </div>
      </header>

      <main className="landing-content">
        <section className="landing-copy">
          <div className="eyebrow">
            <span className="eyebrow-dot" />
            Intelligent payment infrastructure
          </div>

          <h1>
            Payments built for
            <span> certainty.</span>
          </h1>

          <p className="landing-description">
            Execute payments with idempotent
            protection, transaction reconciliation
            and intelligent anomaly detection —
            all through one control platform.
          </p>

          <div className="landing-actions">
            <button
              type="button"
              className="gradient-button"
              onClick={() =>
                setAuthMode("register")
              }
            >
              Start building
              <Icon name="arrow" size={18} />
            </button>

            <div className="landing-security">
              <span className="security-icon">
                <Icon
                  name="shield"
                  size={17}
                />
              </span>

              <span>
                Secure transaction control
              </span>
            </div>
          </div>

          <div className="landing-features">
            <LandingFeature
              icon="shield"
              title="Idempotent"
              text="Duplicate-safe execution"
            />

            <LandingFeature
              icon="refresh"
              title="Reconciled"
              text="Unknown outcomes resolved"
            />

            <LandingFeature
              icon="spark"
              title="Intelligent"
              text="ML-powered anomaly signals"
            />
          </div>
        </section>

        <section className="landing-visual">
          <PaymentNetworkVisual />
        </section>
      </main>

      <section className="auth-panel">
        <div className="auth-panel-heading">
          <span className="auth-panel-label">
            {authMode === "login"
              ? "Welcome back"
              : "Create your account"}
          </span>

          <h2>
            {authMode === "login"
              ? "Sign in to your control center"
              : "Start with a secure account"}
          </h2>

          <p>
            {authMode === "login"
              ? "Access payments, transactions and risk intelligence."
              : "Create an account to access the payment control platform."}
          </p>
        </div>

        <div className="auth-tabs-modern">
          <button
            type="button"
            className={
              authMode === "login"
                ? "active"
                : ""
            }
            onClick={() =>
              setAuthMode("login")
            }
          >
            Sign in
          </button>

          <button
            type="button"
            className={
              authMode === "register"
                ? "active"
                : ""
            }
            onClick={() =>
              setAuthMode("register")
            }
          >
            Register
          </button>
        </div>

        <form
          className="auth-form-modern"
          onSubmit={onSubmit}
        >
          <div className="field-group">
            <label htmlFor="auth-email">
              Email address
            </label>

            <div className="input-shell">
              <Icon name="profile" size={18} />

              <input
                id="auth-email"
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(
                    event.target.value,
                  )
                }
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </div>
          </div>

          <div className="field-group">
            <label htmlFor="auth-password">
              Password
            </label>

            <div className="input-shell">
              <Icon name="shield" size={18} />

              <input
                id="auth-password"
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value,
                  )
                }
                placeholder="Enter your password"
                autoComplete={
                  authMode === "login"
                    ? "current-password"
                    : "new-password"
                }
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="gradient-button auth-submit"
            disabled={loading}
          >
            {loading
              ? "Please wait..."
              : authMode === "login"
                ? "Sign in"
                : "Create account"}

            {!loading && (
              <Icon
                name="arrow"
                size={17}
              />
            )}
          </button>
        </form>

        {message && (
          <div className="auth-feedback success">
            <Icon name="check" size={16} />
            <span>{message}</span>
          </div>
        )}

        {error && (
          <div className="auth-feedback error">
            <Icon name="close" size={16} />
            <span>{error}</span>
          </div>
        )}
      </section>

      <LandingFooter />
    </div>
  );
}

function LandingFeature({
  icon,
  title,
  text,
}) {
  return (
    <div className="landing-feature">
      <span className="landing-feature-icon">
        <Icon name={icon} size={17} />
      </span>

      <div>
        <strong>{title}</strong>
        <span>{text}</span>
      </div>
    </div>
  );
}

function PaymentNetworkVisual() {
  return (
    <div className="network-card">
      <div className="network-glow" />

      <div className="network-card-header">
        <div>
          <span>Transaction network</span>
          <strong>Live processing</strong>
        </div>

        <span className="live-pill">
          <span />
          LIVE
        </span>
      </div>

      <div className="network-canvas">
        <div className="network-grid" />

        <div className="network-line line-one" />
        <div className="network-line line-two" />
        <div className="network-line line-three" />
        <div className="network-line line-four" />

        <NetworkNode
          className="node-one"
          label="Client"
          icon="profile"
        />

        <NetworkNode
          className="node-two"
          label="Payment"
          icon="payment"
          active
        />

        <NetworkNode
          className="node-three"
          label="Processor"
          icon="activity"
        />

        <NetworkNode
          className="node-four"
          label="Risk"
          icon="spark"
        />

        <div className="network-center">
          <div className="network-center-ring">
            <div>
              <Icon
                name="shield"
                size={28}
              />
            </div>
          </div>

          <strong>Protected</strong>
          <span>Transaction execution</span>
        </div>

        <div className="network-floating-card floating-card-one">
          <span className="mini-status success" />
          <div>
            <strong>TXN-84291</strong>
            <span>₹12,500.00</span>
          </div>
          <Icon name="check" size={15} />
        </div>

        <div className="network-floating-card floating-card-two">
          <span className="mini-status anomaly" />
          <div>
            <strong>Risk signal</strong>
            <span>12.4 · Low</span>
          </div>
          <Icon name="spark" size={15} />
        </div>
      </div>

      <div className="network-card-footer">
        <div>
          <span>Processing reliability</span>
          <strong>99.98%</strong>
        </div>

        <div className="network-footer-bar">
          <span />
        </div>
      </div>
    </div>
  );
}

function NetworkNode({
  className,
  label,
  icon,
  active = false,
}) {
  return (
    <div
      className={`network-node ${className} ${
        active ? "active" : ""
      }`}
    >
      <div>
        <Icon name={icon} size={17} />
      </div>
      <span>{label}</span>
    </div>
  );
}

/* =========================================================
   APPLICATION SHELL
   ========================================================= */

function Brand() {
  return (
    <div className="brand">
      <div className="brand-symbol">
        <span>P</span>
        <span>E</span>
      </div>

      <div className="brand-copy">
        <strong>Payment Engine</strong>
        <span>Transaction intelligence</span>
      </div>
    </div>
  );
}

function Sidebar({
  view,
  navigate,
  logout,
  historyCount,
}) {
  const navigation = [
    {
      id: "dashboard",
      label: "Overview",
      icon: "dashboard",
    },
    {
      id: "payment",
      label: "New payment",
      icon: "payment",
    },
    {
      id: "history",
      label: "Transactions",
      icon: "transactions",
      badge: historyCount,
    },
    {
      id: "risk",
      label: "Risk intelligence",
      icon: "risk",
    },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <Brand />

        <div className="sidebar-section-label">
          Workspace
        </div>

        <nav className="sidebar-nav">
          {navigation.map((item) => (
            <button
              key={item.id}
              type="button"
              className={
                view === item.id
                  ? "sidebar-link active"
                  : "sidebar-link"
              }
              onClick={() =>
                navigate(item.id)
              }
            >
              <span className="sidebar-link-icon">
                <Icon
                  name={item.icon}
                  size={19}
                />
              </span>

              <span className="sidebar-link-text">
                {item.label}
              </span>

              {item.badge > 0 && (
                <span className="sidebar-badge">
                  {item.badge}
                </span>
              )}

              {view === item.id && (
                <span className="sidebar-active-line" />
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-section-label secondary">
          Account
        </div>

        <button
          type="button"
          className={
            view === "profile"
              ? "sidebar-link active"
              : "sidebar-link"
          }
          onClick={() =>
            navigate("profile")
          }
        >
          <span className="sidebar-link-icon">
            <Icon name="profile" size={19} />
          </span>

          <span className="sidebar-link-text">
            Profile
          </span>

          {view === "profile" && (
            <span className="sidebar-active-line" />
          )}
        </button>
      </div>

      <div className="sidebar-bottom">
        <div className="sidebar-security-card">
          <span className="sidebar-security-icon">
            <Icon name="shield" size={17} />
          </span>

          <div>
            <strong>Protected workspace</strong>
            <span>JWT authenticated</span>
          </div>
        </div>

        <button
          type="button"
          className="sidebar-logout"
          onClick={logout}
        >
          <Icon name="logoutSmall" size={18} />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
}

function Topbar({
  view,
  monitoring,
  onProfile,
}) {
  const pageDetails = {
    dashboard: {
      title: "Good to see you",
      subtitle:
        "Monitor your payment operations in real time.",
    },

    payment: {
      title: "New payment",
      subtitle:
        "Create a protected payment transaction.",
    },

    history: {
      title: "Transactions",
      subtitle:
        "Review payment execution and processor outcomes.",
    },

    receipt: {
      title: "Payment receipt",
      subtitle:
        "Detailed transaction execution record.",
    },

    risk: {
      title: "Risk intelligence",
      subtitle:
        "Inspect anomaly and transaction risk signals.",
    },

    profile: {
      title: "Your profile",
      subtitle:
        "Manage your account information.",
    },
  };

  const details =
    pageDetails[view] ||
    pageDetails.dashboard;

  return (
    <header className="topbar-modern">
      <div className="topbar-copy">
        <div className="breadcrumb">
          Payment Engine
          <Icon name="chevron" size={13} />
          <span>{details.title}</span>
        </div>

        <h1>{details.title}</h1>
        <p>{details.subtitle}</p>
      </div>

      <div className="topbar-actions">
        <div className="system-health">
          <span
            className={
              monitoring
                ? "health-dot"
                : "health-dot checking"
            }
          />

          <div>
            <strong>
              {monitoring
                ? "Systems operational"
                : "Checking systems"}
            </strong>

            <span>
              {monitoring
                ? "All services responding"
                : "Connecting to backend"}
            </span>
          </div>
        </div>

        <button
          type="button"
          className="profile-trigger"
          onClick={onProfile}
          aria-label="Open profile"
        >
          <span className="avatar">
            PE
          </span>

          <Icon
            name="chevron"
            size={15}
          />
        </button>
      </div>
    </header>
  );
}

/* =========================================================
   DASHBOARD
   ========================================================= */

function Dashboard({
  stats,
  history,
  monitoring,
  onTransaction,
  onNewPayment,
  onTransactions,
  onRisk,
}) {
  return (
    <div className="page-enter">
      <section className="dashboard-hero">
        <div className="dashboard-hero-content">
          <div className="eyebrow dashboard-eyebrow">
            <span className="eyebrow-dot" />
            Payment control center
          </div>

          <h2>
            Every transaction.
            <span> Accounted for.</span>
          </h2>

          <p>
            Track execution, identify unknown outcomes
            and keep payment operations under control.
          </p>

          <button
            type="button"
            className="gradient-button"
            onClick={onNewPayment}
          >
            <Icon name="plus" size={17} />
            Create payment
          </button>
        </div>

        <div className="dashboard-hero-visual">
          <div className="hero-orbit orbit-one" />
          <div className="hero-orbit orbit-two" />
          <div className="hero-orbit orbit-three" />

          <div className="hero-core">
            <Icon name="shield" size={31} />
          </div>

          <span className="hero-particle particle-one" />
          <span className="hero-particle particle-two" />
          <span className="hero-particle particle-three" />
        </div>
      </section>

      <section className="metrics-grid-modern">
        <MetricCard
          label="Total transactions"
          value={stats.total}
          icon="transactions"
          trend={
            stats.total > 0
              ? "Activity recorded"
              : "No activity yet"
          }
          accent="blue"
        />

        <MetricCard
          label="Successful"
          value={stats.successful}
          icon="check"
          trend={
            stats.total
              ? `${Math.round(
                  (stats.successful /
                    stats.total) *
                    100,
                )}% of total`
              : "Ready for payments"
          }
          accent="green"
        />

        <MetricCard
          label="Failed"
          value={stats.failed}
          icon="close"
          trend={
            stats.failed
              ? "Requires attention"
              : "No failed payments"
          }
          accent="red"
        />

        <MetricCard
          label="Unknown / pending"
          value={stats.unknown}
          icon="clock"
          trend={
            stats.unknown
              ? "Reconciliation queue"
              : "No unresolved outcomes"
          }
          accent="amber"
        />
      </section>

      <section className="dashboard-grid">
        <div className="surface-card recent-transactions">
          <div className="surface-card-header">
            <div>
              <span className="section-kicker">
                Activity
              </span>

              <h3>Recent transactions</h3>

              <p>
                Latest payment execution activity.
              </p>
            </div>

            <button
              type="button"
              className="text-button"
              onClick={onTransactions}
            >
              View all
              <Icon name="arrow" size={15} />
            </button>
          </div>

          {history.length === 0 ? (
            <EmptyState
              icon="transactions"
              title="No transactions yet"
              text="Your payment activity will appear here."
              actionLabel="Create first payment"
              onAction={onNewPayment}
            />
          ) : (
            <div className="modern-transaction-list">
              {history
                .slice(0, 6)
                .map((transaction) => (
                  <TransactionItem
                    key={transaction.id}
                    transaction={transaction}
                    onClick={() =>
                      onTransaction(
                        transaction,
                      )
                    }
                  />
                ))}
            </div>
          )}
        </div>

        <div className="surface-card intelligence-card">
          <div className="surface-card-header">
            <div>
              <span className="section-kicker">
                Intelligence
              </span>

              <h3>Risk & anomaly</h3>

              <p>
                ML-powered transaction signals.
              </p>
            </div>

            <span className="intelligence-icon">
              <Icon name="spark" size={18} />
            </span>
          </div>

          <div className="intelligence-visual">
            <div className="intelligence-ring">
              <div>
                <Icon name="shield" size={23} />
              </div>
            </div>

            <div>
              <strong>
                {history.length
                  ? "Monitoring active"
                  : "Ready for analysis"}
              </strong>

              <span>
                {history.length
                  ? "Transaction risk signals are being evaluated."
                  : "Create a transaction to generate risk signals."}
              </span>
            </div>
          </div>

          <button
            type="button"
            className="outline-button full-width"
            onClick={onRisk}
          >
            Open risk intelligence
            <Icon name="arrow" size={16} />
          </button>
        </div>
      </section>

      <section className="system-overview">
        <div>
          <span className="section-kicker">
            Infrastructure
          </span>

          <h3>Payment engine status</h3>

          <p>
            Your application services are monitored
            through the backend monitoring API.
          </p>
        </div>

        <div className="service-status-list">
          <ServiceStatus
            label="API"
            active={Boolean(monitoring)}
          />

          <ServiceStatus
            label="Database"
            active={Boolean(monitoring)}
          />

          <ServiceStatus
            label="Event pipeline"
            active={Boolean(monitoring)}
          />

          <ServiceStatus
            label="Risk pipeline"
            active={Boolean(monitoring)}
          />
        </div>
      </section>
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon,
  trend,
  accent,
}) {
  return (
    <div
      className={`metric-card-modern accent-${accent}`}
    >
      <div className="metric-card-top">
        <span className="metric-icon">
          <Icon name={icon} size={18} />
        </span>

        <Icon
          name="arrowUp"
          size={15}
        />
      </div>

      <span className="metric-label">
        {label}
      </span>

      <strong className="metric-value">
        {value}
      </strong>

      <span className="metric-trend">
        {trend}
      </span>
    </div>
  );
}

function ServiceStatus({
  label,
  active,
}) {
  return (
    <div className="service-status">
      <span
        className={
          active
            ? "service-status-dot"
            : "service-status-dot checking"
        }
      />

      <span>{label}</span>

      <strong>
        {active
          ? "Operational"
          : "Checking"}
      </strong>
    </div>
  );
}

/* =========================================================
   PAYMENT
   ========================================================= */

function PaymentPage({
  receiverName,
  setReceiverName,
  receiverDetails,
  setReceiverDetails,
  amount,
  setAmount,
  loading,
  onSubmit,
  onCancel,
}) {
  return (
    <div className="page-enter">
      <section className="payment-layout">
        <div className="surface-card payment-main-card">
          <div className="surface-card-header">
            <div>
              <span className="section-kicker">
                Payment request
              </span>

              <h3>Send a payment</h3>

              <p>
                Enter the beneficiary details and
                amount to initiate a payment.
              </p>
            </div>

            <span className="secure-badge">
              <Icon name="shield" size={14} />
              Protected
            </span>
          </div>

          <form
            className="modern-payment-form"
            onSubmit={onSubmit}
          >
            <div className="form-section-title">
              <span>01</span>
              Beneficiary details
            </div>

            <div className="form-grid-modern">
              <Field
                label="Receiver name"
                value={receiverName}
                onChange={setReceiverName}
                placeholder="e.g. Revanth Kumar"
              />

              <Field
                label="Amount"
                type="number"
                value={amount}
                onChange={setAmount}
                placeholder="1.00"
                min="1.00"
                step="0.01"
              />

              <div className="field-group modern-field full-width-field">
                <label>Receiver details / UPI ID</label>

                <input
                  type="text"
                  value={receiverDetails}
                  onChange={(event) =>
                    setReceiverDetails(
                      event.target.value,
                    )
                  }
                  placeholder="e.g. receiver@upi or account details"
                  required
                />
              </div>
            </div>

            <div className="payment-info-strip">
              <div className="payment-info-icon">
                <Icon
                  name="shield"
                  size={17}
                />
              </div>

              <div>
                <strong>Secure payment initiation</strong>

                <span>
                  Payments are processed in INR with
                  duplicate-protection and transaction
                  status controls.
                </span>
              </div>
            </div>

            <div className="payment-form-actions">
              <button
                type="button"
                className="outline-button"
                onClick={onCancel}
                disabled={loading}
              >
                Cancel
              </button>

              <button
                type="submit"
                className="gradient-button"
                disabled={loading}
              >
                {loading
                  ? "Processing..."
                  : "Send payment"}

                {!loading && (
                  <Icon
                    name="arrow"
                    size={17}
                  />
                )}
              </button>
            </div>
          </form>
        </div>

        <aside className="payment-side-card">
          <div className="payment-side-glow" />

          <span className="section-kicker light">
            Payment controls
          </span>

          <h3>
            Secure payment.
            <span> Clear status.</span>
          </h3>

          <p>
            Track payment initiation, processing and
            settlement status from a single operations
            view.
          </p>

          <div className="payment-flow">
            <PaymentFlowStep
              number="01"
              title="Initiate"
              text="Beneficiary details verified"
              active
            />

            <PaymentFlowStep
              number="02"
              title="Process"
              text="Payment submitted for processing"
            />

            <PaymentFlowStep
              number="03"
              title="Settle"
              text="Final transaction status recorded"
            />
          </div>

          <div className="payment-side-footer">
            <Icon name="shield" size={17} />
            <span>
              Transaction controls enabled
            </span>
          </div>
        </aside>
      </section>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  min,
  step,
}) {
  return (
    <div className="field-group modern-field">
      <label>{label}</label>

      <input
        type={type}
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        placeholder={placeholder}
        min={min}
        step={step}
        required
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}) {
  return (
    <div className="field-group modern-field">
      <label>{label}</label>

      <select
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        required
      >
        {options.map(
          ([optionValue, optionLabel]) => (
            <option
              key={optionValue}
              value={optionValue}
            >
              {optionLabel}
            </option>
          ),
        )}
      </select>
    </div>
  );
}

function PaymentFlowStep({
  number,
  title,
  text,
  active = false,
}) {
  return (
    <div
      className={`payment-flow-step ${
        active ? "active" : ""
      }`}
    >
      <span>{number}</span>

      <div>
        <strong>{title}</strong>
        <p>{text}</p>
      </div>

      {active && (
        <Icon
          name="check"
          size={15}
        />
      )}
    </div>
  );
}

/* =========================================================
   TRANSACTIONS
   ========================================================= */

function TransactionHistory({
  history,
  onReceipt,
  onRisk,
  onReconcile,
}) {
  return (
    <div className="page-enter">
      <section className="surface-card">
        <div className="surface-card-header">
          <div>
            <span className="section-kicker">
              Ledger activity
            </span>

            <h3>Transaction history</h3>

            <p>
              Payment and processor results recorded
              by the application.
            </p>
          </div>

          <span className="count-pill">
            {history.length} records
          </span>
        </div>

        {history.length === 0 ? (
          <EmptyState
            icon="transactions"
            title="No transaction history"
            text="Create a payment to start building your transaction history."
          />
        ) : (
          <div className="transaction-table-wrapper">
            <table className="modern-table">
              <thead>
                <tr>
                  <th>Transaction</th>
                  <th>Amount</th>
                  <th>Provider</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {history.map(
                  (transaction) => (
                    <tr
                      key={transaction.id}
                    >
                      <td>
                        <div className="table-transaction">
                          <span className="transaction-avatar">
                            <Icon
                              name="payment"
                              size={16}
                            />
                          </span>

                          <div>
                            <strong>
                              {
                                transaction.transaction_reference
                              }
                            </strong>

                            <span>
                              {transaction.merchant_reference ||
                                "Payment intent"}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td>
                        <strong>
                          {
                            transaction.currency
                          }{" "}
                          {Number(
                            transaction.amount,
                          ).toFixed(2)}
                        </strong>
                      </td>

                      <td>
                        <span className="provider-pill">
                          {
                            transaction.provider
                          }
                        </span>
                      </td>

                      <td>
                        <StatusBadge
                          status={
                            transaction.status
                          }
                        />
                      </td>

                      <td>
                        <span className="table-date">
                          {new Date(
                            transaction.created_at,
                          ).toLocaleString()}
                        </span>
                      </td>

                      <td>
                        <div className="table-actions">
                          <button
                            type="button"
                            onClick={() =>
                              onReceipt(
                                transaction,
                              )
                            }
                          >
                            Receipt
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              onRisk(
                                transaction,
                              )
                            }
                          >
                            Risk
                          </button>

                          {transaction.status ===
                            "UNKNOWN" && (
                            <button
                              type="button"
                              className="reconcile-action"
                              onClick={() =>
                                onReconcile(
                                  transaction,
                                )
                              }
                            >
                              Reconcile
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function TransactionItem({
  transaction,
  onClick,
}) {
  return (
    <button
      type="button"
      className="modern-transaction-item"
      onClick={onClick}
    >
      <span className="transaction-icon">
        <Icon name="payment" size={17} />
      </span>

      <span className="transaction-main">
        <strong>
          {transaction.transaction_reference}
        </strong>

        <span>
          {transaction.provider} ·{" "}
          {transaction.merchant_reference ||
            "Payment"}
        </span>
      </span>

      <span className="transaction-amount">
        {transaction.currency}{" "}
        {Number(
          transaction.amount,
        ).toFixed(2)}
      </span>

      <StatusBadge
        status={transaction.status}
      />

      <Icon
        name="chevron"
        size={16}
      />
    </button>
  );
}

/* =========================================================
   RECEIPT
   ========================================================= */

function Receipt({
  transaction,
  onRisk,
  onReconcile,
  onBack,
}) {
  const successful =
    transaction.status === "SUCCESS";

  return (
    <div className="page-enter">
      <section className="receipt-layout">
        <div className="receipt-card">
          <div
            className={`receipt-status-visual ${
              successful
                ? "success"
                : transaction.status ===
                    "UNKNOWN"
                  ? "unknown"
                  : "failed"
            }`}
          >
            <div className="receipt-status-icon">
              <Icon
                name={
                  successful
                    ? "check"
                    : transaction.status ===
                        "UNKNOWN"
                      ? "clock"
                      : "close"
                }
                size={29}
              />
            </div>

            <span>
              {successful
                ? "Payment successful"
                : transaction.status ===
                    "UNKNOWN"
                  ? "Payment outcome unknown"
                  : "Payment failed"}
            </span>

            <strong>
              {transaction.currency}{" "}
              {Number(
                transaction.amount,
              ).toFixed(2)}
            </strong>

            <p>
              {successful
                ? "The transaction was successfully processed."
                : transaction.status ===
                    "UNKNOWN"
                  ? "The processor outcome requires reconciliation."
                  : "The processor reported a failed transaction."}
            </p>
          </div>

          <div className="receipt-divider" />

          <div className="receipt-details-grid">
            <ReceiptDetail
              label="Transaction reference"
              value={
                transaction.transaction_reference
              }
            />

            <ReceiptDetail
              label="Payment intent"
              value={
                transaction.payment_intent_id
              }
            />

            <ReceiptDetail
              label="Provider"
              value={
                transaction.provider
              }
            />

            <ReceiptDetail
              label="Provider transaction ID"
              value={
                transaction.provider_transaction_id ||
                "Not assigned"
              }
            />

            <ReceiptDetail
              label="Merchant reference"
              value={
                transaction.merchant_reference ||
                "Not available"
              }
            />

            <ReceiptDetail
              label="Created"
              value={new Date(
                transaction.created_at,
              ).toLocaleString()}
            />
          </div>

          <div className="receipt-actions-modern">
            <button
              type="button"
              className="outline-button"
              onClick={onBack}
            >
              Back to transactions
            </button>

            <button
              type="button"
              className="outline-button"
              onClick={() =>
                onRisk(transaction)
              }
            >
              <Icon
                name="spark"
                size={16}
              />
              View risk
            </button>

            {transaction.status ===
              "UNKNOWN" && (
              <button
                type="button"
                className="gradient-button"
                onClick={() =>
                  onReconcile(
                    transaction,
                  )
                }
              >
                <Icon
                  name="refresh"
                  size={16}
                />
                Reconcile
              </button>
            )}
          </div>
        </div>

        <aside className="receipt-side-panel">
          <span className="section-kicker">
            Transaction lifecycle
          </span>

          <h3>
            Execution
            <span> complete.</span>
          </h3>

          <div className="lifecycle">
            <LifecycleStep
              title="Payment intent"
              text="Created"
              completed
            />

            <LifecycleStep
              title="Transaction"
              text="Processed"
              completed
            />

            <LifecycleStep
              title="Processor"
              text={transaction.status}
              completed={
                transaction.status !==
                "UNKNOWN"
              }
              warning={
                transaction.status ===
                "UNKNOWN"
              }
            />

            <LifecycleStep
              title="Reconciliation"
              text={
                transaction.status ===
                "UNKNOWN"
                  ? "Required"
                  : "Not required"
              }
              completed={
                transaction.status !==
                "UNKNOWN"
              }
            />
          </div>
        </aside>
      </section>
    </div>
  );
}

function ReceiptDetail({
  label,
  value,
}) {
  return (
    <div className="receipt-detail">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function LifecycleStep({
  title,
  text,
  completed,
  warning,
}) {
  return (
    <div className="lifecycle-step">
      <span
        className={
          warning
            ? "lifecycle-icon warning"
            : completed
              ? "lifecycle-icon completed"
              : "lifecycle-icon"
        }
      >
        <Icon
          name={
            warning
              ? "clock"
              : completed
                ? "check"
                : "activity"
          }
          size={14}
        />
      </span>

      <div>
        <strong>{title}</strong>
        <span>{text}</span>
      </div>
    </div>
  );
}

/* =========================================================
   RISK
   ========================================================= */

function RiskDashboard({
  transaction,
  risk,
  history,
  onLoadRisk,
}) {
  return (
    <div className="page-enter">
      <section className="risk-page-grid">
        <div className="surface-card risk-main-card">
          <div className="surface-card-header">
            <div>
              <span className="section-kicker">
                Machine learning
              </span>

              <h3>Risk intelligence</h3>

              <p>
                Persisted anomaly assessment from
                the ML pipeline.
              </p>
            </div>

            <span className="intelligence-icon">
              <Icon name="spark" size={18} />
            </span>
          </div>

          {!risk ? (
            <div className="risk-empty">
              <div className="risk-empty-icon">
                <Icon
                  name="spark"
                  size={24}
                />
              </div>

              <h4>
                {transaction
                  ? "Assessment is processing"
                  : "Select a transaction"}
              </h4>

              <p>
                {transaction
                  ? "The ML event pipeline may still be processing this transaction."
                  : "Choose a transaction from the list to inspect its risk assessment."}
              </p>
            </div>
          ) : (
            <RiskResult risk={risk} />
          )}
        </div>

        <div className="surface-card risk-list-card">
          <div className="surface-card-header">
            <div>
              <span className="section-kicker">
                Monitoring
              </span>

              <h3>Transactions</h3>
            </div>
          </div>

          <div className="risk-selection-list">
            {history.length === 0 ? (
              <EmptyState
                icon="risk"
                title="No transactions"
                text="Risk assessments will appear after transactions are processed."
              />
            ) : (
              history.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  className={
                    transaction?.id ===
                    item.id
                      ? "risk-selection active"
                      : "risk-selection"
                  }
                  onClick={() =>
                    onLoadRisk(item)
                  }
                >
                  <span className="risk-selection-icon">
                    <Icon
                      name="activity"
                      size={16}
                    />
                  </span>

                  <span>
                    <strong>
                      {
                        item.transaction_reference
                      }
                    </strong>

                    <small>
                      {item.currency}{" "}
                      {Number(
                        item.amount,
                      ).toFixed(2)}
                    </small>
                  </span>

                  <StatusBadge
                    status={
                      item.status
                    }
                  />

                  <Icon
                    name="chevron"
                    size={14}
                  />
                </button>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function RiskResult({ risk }) {
  const score = Number(
    risk.risk_score,
  );

  const normalizedScore = Math.min(
    Math.max(score, 0),
    100,
  );

  const levelClass =
    risk.risk_level.toLowerCase();

  return (
    <div className="risk-result">
      <div className="risk-score-hero">
        <div
          className={`risk-score-ring ${levelClass}`}
          style={{
            "--risk-progress": `${normalizedScore}%`,
          }}
        >
          <div>
            <strong>
              {score.toFixed(2)}
            </strong>

            <span>/ 100</span>
          </div>
        </div>

        <div className="risk-score-copy">
          <span>Risk score</span>

          <strong>
            {risk.risk_level}
          </strong>

          <p>
            {risk.is_anomaly
              ? "Anomaly detected by the selected model."
              : "No anomaly detected for this transaction."}
          </p>
        </div>
      </div>

      <div className="risk-metrics">
        <RiskMetric
          label="Model"
          value={risk.model_name}
          icon="spark"
        />

        <RiskMetric
          label="Anomaly score"
          value={Number(
            risk.anomaly_score,
          ).toFixed(6)}
          icon="activity"
        />

        <RiskMetric
          label="Detection"
          value={
            risk.is_anomaly
              ? "Detected"
              : "Normal"
          }
          icon={
            risk.is_anomaly
              ? "risk"
              : "check"
          }
        />

        <RiskMetric
          label="Transaction"
          value={
            risk.transaction_reference
          }
          icon="payment"
        />
      </div>
    </div>
  );
}

function RiskMetric({
  label,
  value,
  icon,
}) {
  return (
    <div className="risk-metric">
      <span className="risk-metric-icon">
        <Icon name={icon} size={15} />
      </span>

      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

/* =========================================================
   PROFILE
   ========================================================= */

function ProfilePage({
  email,
  displayName,
  onSave,
  onBack,
}) {
  const [editing, setEditing] =
    useState(false);

  const [draftName, setDraftName] =
    useState(displayName);

  function handleSave() {
    const saved = onSave(draftName);

    if (saved) {
      setEditing(false);
    }
  }

  function handleCancel() {
    setDraftName(displayName);
    setEditing(false);
  }

  return (
    <div className="page-enter">
      <section className="profile-page-grid">
        <div className="surface-card profile-main-card">
          <div className="profile-cover">
            <div className="profile-cover-orb" />
          </div>

          <div className="profile-main-content">
            <div className="profile-heading">
              <div className="large-avatar">
                {(
                  displayName ||
                  email ||
                  "PE"
                )
                  .slice(0, 2)
                  .toUpperCase()}
              </div>

              <div className="profile-heading-copy">
                <span className="section-kicker">
                  Account profile
                </span>

                <h3>
                  {displayName || "Your profile"}
                </h3>

                <p>{email}</p>
              </div>

              {!editing ? (
                <button
                  type="button"
                  className="outline-button profile-edit-button"
                  onClick={() =>
                    setEditing(true)
                  }
                >
                  <Icon
                    name="profile"
                    size={16}
                  />
                  Edit profile
                </button>
              ) : (
                <div className="profile-action-group">
                  <button
                    type="button"
                    className="outline-button"
                    onClick={handleCancel}
                  >
                    Cancel
                  </button>

                  <button
                    type="button"
                    className="gradient-button"
                    onClick={handleSave}
                    disabled={!draftName.trim()}
                  >
                    <Icon
                      name="check"
                      size={16}
                    />
                    Save changes
                  </button>
                </div>
              )}
            </div>

            <div className="profile-divider" />

            <div className="profile-form">
              <div className="form-section-title">
                <span>01</span>
                Personal information
              </div>

              <div className="profile-form-grid">
                <div className="field-group modern-field">
                  <label>Display name</label>

                  <input
                    value={draftName}
                    onChange={(event) =>
                      setDraftName(
                        event.target.value,
                      )
                    }
                    placeholder="Add your name"
                    disabled={!editing}
                  />
                </div>

                <div className="field-group modern-field">
                  <label>Email address</label>

                  <input
                    value={email}
                    disabled
                    readOnly
                  />
                </div>
              </div>

              {editing && (
                <div className="profile-edit-note">
                  <Icon
                    name="check"
                    size={16}
                  />

                  <span>
                    Update your display name and save
                    the changes to this account.
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        <aside className="profile-security-card">
          <div className="profile-security-icon">
            <Icon
              name="shield"
              size={24}
            />
          </div>

          <span className="section-kicker light">
            Account security
          </span>

          <h3>
            Your account is
            <span> protected.</span>
          </h3>

          <p>
            Your session is secured with access and
            refresh tokens for authenticated payment
            operations.
          </p>

          <div className="security-status">
            <span />
            Authenticated session
          </div>

          <button
            type="button"
            className="profile-back-button"
            onClick={onBack}
          >
            Return to dashboard
            <Icon
              name="arrow"
              size={16}
            />
          </button>
        </aside>
      </section>
    </div>
  );
}

/* =========================================================
   SHARED UI
   ========================================================= */

function StatusBadge({
  status,
}) {
  const normalized =
    status.toLowerCase();

  const icon =
    status === "SUCCESS"
      ? "check"
      : status === "FAILED"
        ? "close"
        : status === "UNKNOWN" ||
            status ===
              "RECONCILING"
          ? "clock"
          : "activity";

  return (
    <span
      className={`status-badge-modern status-${normalized}`}
    >
      <Icon name={icon} size={12} />
      {status}
    </span>
  );
}

function EmptyState({
  icon,
  title,
  text,
  actionLabel,
  onAction,
}) {
  return (
    <div className="empty-state-modern">
      <div className="empty-state-icon">
        <Icon name={icon} size={23} />
      </div>

      <h4>{title}</h4>
      <p>{text}</p>

      {actionLabel && (
        <button
          type="button"
          className="outline-button"
          onClick={onAction}
        >
          {actionLabel}
          <Icon name="arrow" size={15} />
        </button>
      )}
    </div>
  );
}

function Footer() {
  return (
    <footer className="application-footer">
      <div>
        <Brand />
      </div>

      <div className="footer-center">
        <span>
          Idempotent execution
        </span>

        <span>
          Reconciliation
        </span>

        <span>
          Risk intelligence
        </span>
      </div>

      <span className="footer-copy">
        © 2026 Payment Engine
      </span>
    </footer>
  );
}

function LandingFooter() {
  return (
    <footer className="landing-footer">
      <div>
        <strong>Payment Engine</strong>
        <span>
          Intelligent payment processing &
          transaction control
        </span>
      </div>

      <div className="landing-footer-links">
        <span>Idempotency</span>
        <span>Reconciliation</span>
        <span>Risk intelligence</span>
      </div>

      <span>
        © 2026 Payment Engine
      </span>
    </footer>
  );
}

export default App;