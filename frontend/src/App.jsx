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
  const [receiverAccount, setReceiverAccount] =
    useState("");
  const [amount, setAmount] = useState("");

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

  async function handleAuth(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setMessage("");

    try {
      if (authMode === "register") {
        await registerUser(email, password);

        setMessage(
          "Registration successful. You can now log in.",
        );

        setAuthMode("login");
      } else {
        await loginUser(email, password);

        setAuthenticated(true);
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
    setView("dashboard");
  }

  async function handlePayment(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const trimmedReceiverName =
        receiverName.trim();

      const trimmedReceiverAccount =
        receiverAccount.trim();

      const numericAmount =
        Number(amount);

      // Receiver name:
      // - Must start with a letter
      // - May contain letters, numbers, and spaces
      // - Must not be numeric-only
      const receiverNamePattern =
        /^[A-Za-z][A-Za-z0-9 ]*$/;

      if (!receiverNamePattern.test(trimmedReceiverName)) {
        throw new Error(
          "Receiver name must contain only letters or alphanumeric characters and must start with a letter.",
        );
      }

      // Receiver account / UPI ID:
      // Example:
      // receiver@bank
      // revanth123@hdfc
      // user01@sbi
      const receiverAccountPattern =
        /^[A-Za-z0-9]+@[A-Za-z0-9]+$/;

      if (
        !receiverAccountPattern.test(
          trimmedReceiverAccount,
        )
      ) {
        throw new Error(
          "Receiver Account / UPI ID must be in the format receiver@bank.",
        );
      }

      // Amount must be strictly greater than ₹1.00.
      if (
        !Number.isFinite(numericAmount) ||
        numericAmount <= 1
      ) {
        throw new Error(
          "Payment amount must be greater than ₹1.00.",
        );
      }

      // Limit to exactly two decimal places.
      if (
        !/^\d+(?:\.\d{1,2})?$/.test(
          amount.trim(),
        )
      ) {
        throw new Error(
          "Payment amount can have at most two decimal places.",
        );
      }

      const paymentIntent =
        await createPaymentIntent({
          merchant_reference: `PAY-${Date.now()}`,
          idempotency_key: crypto.randomUUID(),
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
          trimmedReceiverName,

        receiver_account:
          trimmedReceiverAccount,

        merchant_reference:
          paymentIntent.merchant_reference,

        idempotency_key:
          paymentIntent.idempotency_key,
      };

      setHistory((previous) => {
        const filtered = previous.filter(
          (item) =>
            item.id !== transaction.id,
        );

        return [
          record,
          ...filtered,
        ].slice(0, 50);
      });

      setSelectedTransaction(record);
      setRisk(null);

      setReceiverName("");
      setReceiverAccount("");
      setAmount("");

      setView("receipt");
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
        "Risk assessment is not available yet.",
      );
    }

    setView("risk");
  }

  async function handleReconciliation(transaction) {
    setLoading(true);
    setError("");

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
        (item) => item.status === "UNKNOWN",
      ).length,
    };
  }, [history]);

  if (!authenticated) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <div className="brand-mark">
            PE
          </div>

          <h1>
            Payment Processing Engine
          </h1>

          <p className="muted">
            Idempotent payment processing,
            reconciliation and transaction risk.
          </p>

          <div className="auth-tabs">
            <button
              className={
                authMode === "login"
                  ? "active"
                  : ""
              }
              onClick={() =>
                setAuthMode("login")
              }
            >
              Login
            </button>

            <button
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

          <form onSubmit={handleAuth}>
            <label>Email</label>

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              required
            />

            <label>Password</label>

            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              required
            />

            <button
              className="primary-button"
              disabled={loading}
            >
              {loading
                ? "Please wait..."
                : authMode === "login"
                  ? "Login"
                  : "Create account"}
            </button>
          </form>

          {message && (
            <div className="success-message">
              {message}
            </div>
          )}

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="application">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark small">
            PE
          </div>

          <div>
            <strong>Payment Engine</strong>
            <span>Transaction Control</span>
          </div>
        </div>

        <nav>
          <button
            className={
              view === "dashboard"
                ? "nav-active"
                : ""
            }
            onClick={() =>
              setView("dashboard")
            }
          >
            Dashboard
          </button>

          <button
            className={
              view === "payment"
                ? "nav-active"
                : ""
            }
            onClick={() =>
              setView("payment")
            }
          >
            New Payment
          </button>

          <button
            className={
              view === "history"
                ? "nav-active"
                : ""
            }
            onClick={() =>
              setView("history")
            }
          >
            Transactions
          </button>

          <button
            className={
              view === "risk"
                ? "nav-active"
                : ""
            }
            onClick={() =>
              setView("risk")
            }
          >
            Risk / Anomaly
          </button>
        </nav>

        <button
          className="logout-button"
          onClick={logout}
        >
          Logout
        </button>
      </aside>

      <main className="content">
        <header className="topbar">
          <div>
            <h2>
              {view === "dashboard" &&
                "Operations Dashboard"}

              {view === "payment" &&
                "Create Payment"}

              {view === "history" &&
                "Transaction History"}

              {view === "receipt" &&
                "Payment Receipt"}

              {view === "risk" &&
                "Risk & Anomaly Assessment"}
            </h2>

            <p className="muted">
              Idempotent Payment Processing &
              Transaction Reconciliation Engine
            </p>
          </div>

          <div className="system-status">
            <span
              className={
                monitoring
                  ? "status-dot"
                  : "status-dot offline"
              }
            />

            {monitoring
              ? "Backend healthy"
              : "Checking backend"}
          </div>
        </header>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {view === "dashboard" && (
          <Dashboard
            stats={stats}
            history={history}
            onTransaction={(transaction) => {
              setSelectedTransaction(
                transaction,
              );
              setView("receipt");
            }}
          />
        )}

        {view === "payment" && (
          <section className="panel">
            <div className="panel-header">
              <div>
                <h3>Send Payment</h3>

                <p className="muted">
                  Enter the receiver details and amount.
                </p>
              </div>
            </div>

            <form
              className="payment-form"
              onSubmit={handlePayment}
            >
              <div className="form-grid">
                <div>
                  <label>Receiver Name</label>

                  <input
                    value={receiverName}
                    onChange={(event) =>
                      setReceiverName(event.target.value)
                    }
                    placeholder="Receiver name"
                    autoComplete="name"
                    required
                  />
                </div>

                <div>
                  <label>Receiver Account / UPI ID</label>

                  <input
                    value={receiverAccount}
                    onChange={(event) =>
                      setReceiverAccount(event.target.value)
                    }
                    placeholder="receiver@bank"
                    pattern="[A-Za-z0-9]+@[A-Za-z0-9]+"
                    title="Enter the receiver account or UPI ID in the format receiver@bank."
                    autoComplete="off"
                    required
                  />
                </div>

                <div>
                  <label>Amount</label>

                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={amount}
                    onChange={(event) =>
                      setAmount(event.target.value)
                    }
                    placeholder="1000.00"
                    required
                  />
                </div>

              </div>

              <button
                className="primary-button"
                disabled={loading}
              >
                {loading ? "Processing..." : "Pay"}
              </button>
            </form>
          </section>
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
            onReconcile={
              handleReconciliation
            }
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
      </main>
    </div>
  );
}

function Dashboard({
  stats,
  history,
  onTransaction,
}) {
  return (
    <>
      <section className="metrics-grid">
        <Metric
          label="Transactions"
          value={stats.total}
        />

        <Metric
          label="Successful"
          value={stats.successful}
        />

        <Metric
          label="Failed"
          value={stats.failed}
        />

        <Metric
          label="Unknown"
          value={stats.unknown}
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Recent Transactions</h3>

            <p className="muted">
              Latest payment activity recorded
              by this frontend session.
            </p>
          </div>
        </div>

        {history.length === 0 ? (
          <div className="empty-state">
            No transactions yet.
          </div>
        ) : (
          <div className="transaction-list">
            {history
              .slice(0, 8)
              .map((transaction) => (
                <button
                  className="transaction-row"
                  key={transaction.id}
                  onClick={() =>
                    onTransaction(
                      transaction,
                    )
                  }
                >
                  <div>
                    <strong>
                      {
                        transaction.transaction_reference
                      }
                    </strong>

                    <span>
                      {transaction.provider}
                    </span>
                  </div>

                  <strong>
                    {transaction.currency}{" "}
                    {Number(
                      transaction.amount,
                    ).toFixed(2)}
                  </strong>

                  <StatusBadge
                    status={
                      transaction.status
                    }
                  />
                </button>
              ))}
          </div>
        )}
      </section>
    </>
  );
}

function TransactionHistory({
  history,
  onReceipt,
  onRisk,
  onReconcile,
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h3>Transactions</h3>

          <p className="muted">
            Payment and processor results.
          </p>
        </div>
      </div>

      {history.length === 0 ? (
        <div className="empty-state">
          No transactions available.
        </div>
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Reference</th>
                <th>Amount</th>
                <th>Provider</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {history.map((transaction) => (
                <tr key={transaction.id}>
                  <td>
                    {
                      transaction.transaction_reference
                    }
                  </td>

                  <td>
                    {transaction.currency}{" "}
                    {Number(
                      transaction.amount,
                    ).toFixed(2)}
                  </td>

                  <td>
                    {transaction.provider}
                  </td>

                  <td>
                    <StatusBadge
                      status={
                        transaction.status
                      }
                    />
                  </td>

                  <td className="actions">
                    <button
                      onClick={() =>
                        onReceipt(
                          transaction,
                        )
                      }
                    >
                      Receipt
                    </button>

                    <button
                      onClick={() =>
                        onRisk(transaction)
                      }
                    >
                      Risk
                    </button>

                    {transaction.status ===
                      "UNKNOWN" && (
                      <button
                        onClick={() =>
                          onReconcile(
                            transaction,
                          )
                        }
                      >
                        Reconcile
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function Receipt({
  transaction,
  onRisk,
  onReconcile,
}) {
  return (
    <section className="panel receipt">
      <div className="receipt-header">
        <div className="receipt-icon">
          ✓
        </div>

        <div>
          <h3>Payment Receipt</h3>

          <p className="muted">
            Transaction execution result
          </p>
        </div>

        <StatusBadge
          status={transaction.status}
        />
      </div>

      <div className="receipt-grid">
        <Detail
          label="Transaction Reference"
          value={
            transaction.transaction_reference
          }
        />

        <Detail
          label="Payment Intent"
          value={
            transaction.payment_intent_id
          }
        />

        <Detail
          label="Provider"
          value={transaction.provider}
        />

        <Detail
          label="Provider Transaction ID"
          value={
            transaction.provider_transaction_id ||
            "Not assigned"
          }
        />

        {transaction.receiver_name && (
          <Detail
            label="Receiver"
            value={transaction.receiver_name}
          />
        )}

        {transaction.receiver_account && (
          <Detail
            label="Receiver Account / UPI ID"
            value={transaction.receiver_account}
          />
        )}

        <Detail
          label="Amount"
          value={`${transaction.currency} ${Number(
            transaction.amount,
          ).toFixed(2)}`}
        />

        <Detail
          label="Created"
          value={new Date(
            transaction.created_at,
          ).toLocaleString()}
        />
      </div>

      <div className="receipt-actions">
        <button
          className="secondary-button"
          onClick={() =>
            onRisk(transaction)
          }
        >
          View Risk Assessment
        </button>

        {transaction.status ===
          "UNKNOWN" && (
          <button
            className="primary-button"
            onClick={() =>
              onReconcile(transaction)
            }
          >
            Reconcile Transaction
          </button>
        )}
      </div>
    </section>
  );
}

function RiskDashboard({
  transaction,
  risk,
  history,
  onLoadRisk,
}) {
  return (
    <section className="risk-layout">
      <div className="panel">
        <div className="panel-header">
          <div>
            <h3>Risk / Anomaly Results</h3>

            <p className="muted">
              Persisted anomaly assessment from
              the ML pipeline.
            </p>
          </div>
        </div>

        {transaction && (
          <div className="selected-transaction">
            <strong>
              {transaction.transaction_reference}
            </strong>

            <span>
              {transaction.currency}{" "}
              {Number(
                transaction.amount,
              ).toFixed(2)}
            </span>
          </div>
        )}

        {!risk ? (
          <div className="empty-state">
            {transaction
              ? "Risk assessment is not available yet. The ML event pipeline may still be processing."
              : "Select a transaction to inspect risk."}
          </div>
        ) : (
          <div>
            <div className="risk-score">
              <span>Risk Score</span>

              <strong>
                {Number(
                  risk.risk_score,
                ).toFixed(2)}
              </strong>
            </div>

            <div className="risk-level">
              <span>Risk Level</span>

              <strong>
                {risk.risk_level}
              </strong>
            </div>

            <div className="risk-detail-grid">
              <Detail
                label="Model"
                value={risk.model_name}
              />

              <Detail
                label="Anomaly"
                value={
                  risk.is_anomaly
                    ? "Detected"
                    : "Not detected"
                }
              />

              <Detail
                label="Anomaly Score"
                value={Number(
                  risk.anomaly_score,
                ).toFixed(6)}
              />

              <Detail
                label="Transaction"
                value={
                  risk.transaction_reference
                }
              />
            </div>
          </div>
        )}
      </div>

      <div className="panel">
        <h3>Risk-ready Transactions</h3>

        <p className="muted">
          Select a transaction to query its
          persisted assessment.
        </p>

        <div className="risk-list">
          {history.map((item) => (
            <button
              key={item.id}
              onClick={() =>
                onLoadRisk(item)
              }
            >
              <span>
                {item.transaction_reference}
              </span>

              <StatusBadge
                status={item.status}
              />
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div className="detail">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function StatusBadge({ status }) {
  return (
    <span
      className={`status-badge status-${status.toLowerCase()}`}
    >
      {status}
    </span>
  );
}

export default App;