"""
Loan Amortization Schedule Calculator
-------------------------------------
Stores loans in SQLite, builds a full Spitzer (French / fixed-payment)
amortization schedule for each one, supports partial and full grace periods,
and summarises every loan with a SQL query.

Run:  python amortization_calculator.py
"""

import sqlite3
from datetime import datetime, timedelta


class AmortizationCalculator:
    """Automatic amortization schedule calculator backed by SQLite."""

    def __init__(self, db_path='loans.db'):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        self.create_tables()

    def create_tables(self):
        """Create the two tables (one loan -> many schedule rows)."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Loans (
                loan_id             INTEGER PRIMARY KEY,
                borrower            TEXT NOT NULL,
                loan_amount         REAL NOT NULL,
                interest_rate       REAL NOT NULL,
                loan_term_months    INTEGER NOT NULL,
                grace_period_months INTEGER NOT NULL DEFAULT 0,
                grace_type          TEXT NOT NULL DEFAULT 'none'
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS PaymentSchedule (
                payment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id         INTEGER NOT NULL,
                month_number    INTEGER NOT NULL,
                payment_date    DATE NOT NULL,
                total_payment   REAL NOT NULL,
                principal       REAL NOT NULL,
                interest        REAL NOT NULL,
                balance         REAL NOT NULL,
                is_grace_period INTEGER DEFAULT 0,

                FOREIGN KEY (loan_id) REFERENCES Loans(loan_id)
            )
        ''')

        self.db.commit()

    def add_loan(self, loan_id, borrower, loan_amount, interest_rate,
                 loan_term_months, grace_period_months=0, grace_type='none'):
        """Add a loan (or replace it, so the script can be re-run safely)."""
        # Parameterised query: values are passed separately from the SQL text,
        # which prevents SQL injection and quoting bugs (e.g. names with ').
        self.cursor.execute('''
            INSERT OR REPLACE INTO Loans
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (loan_id, borrower, loan_amount, interest_rate,
              loan_term_months, grace_period_months, grace_type))
        self.db.commit()
        print(f"Loan #{loan_id} for {borrower} saved.")

    def calculate_monthly_payment(self, principal, annual_rate, months):
        """
        Fixed monthly payment (Spitzer / annuity formula).

        Formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]
        where:
        - P = principal
        - r = monthly interest rate
        - n = number of repayment months (excluding grace months)
        """
        if annual_rate == 0:
            # No interest: the formula divides by zero, so split the principal evenly
            return principal / months

        monthly_rate = annual_rate / 100 / 12
        numerator = monthly_rate * (1 + monthly_rate) ** months
        denominator = (1 + monthly_rate) ** months - 1

        return principal * (numerator / denominator)

    def generate_payment_schedule(self, loan_id):
        """Build the full month-by-month schedule for one loan."""

        # Read the loan details
        self.cursor.execute('SELECT * FROM Loans WHERE loan_id = ?', (loan_id,))
        loan = self.cursor.fetchone()

        if not loan:
            print(f"Loan #{loan_id} not found")
            return

        borrower = loan['borrower']
        principal = loan['loan_amount']
        annual_rate = loan['interest_rate']
        total_months = loan['loan_term_months']
        grace_months = loan['grace_period_months']
        grace_type = loan['grace_type']

        # During grace the principal does not shrink, so the whole principal is
        # repaid over the remaining (non-grace) months.
        payment_amount = self.calculate_monthly_payment(
            principal, annual_rate, total_months - grace_months
        )

        # Remove any previous schedule for this loan, so a re-run recalculates
        # instead of duplicating rows.
        self.cursor.execute('DELETE FROM PaymentSchedule WHERE loan_id = ?', (loan_id,))

        start_date = datetime.now()
        balance = principal

        print(f"\n{'=' * 80}")
        print(f"Amortization schedule - {borrower}")
        print(f"{'=' * 80}")
        print(f"Principal:          {principal:,.2f} ILS")
        print(f"Annual rate:        {annual_rate}%")
        print(f"Term:               {total_months} months (incl. {grace_months} grace months)")
        print(f"Monthly payment:    {payment_amount:,.2f} ILS")
        print(f"{'=' * 80}\n")

        print(f"{'Month':<6} {'Date':<12} {'Payment':>11} {'Interest':>11} "
              f"{'Principal':>11} {'Balance':>12} {'Grace':>6}")
        print("-" * 80)

        for month in range(1, total_months + 1):
            payment_date = start_date + timedelta(days=30 * month)
            is_grace = 1 if month <= grace_months else 0

            if is_grace:
                if grace_type == 'partial':
                    # Partial grace: pay interest only, the debt stays the same
                    monthly_interest = balance * (annual_rate / 100 / 12)
                    monthly_principal = 0
                    monthly_payment = monthly_interest
                else:
                    # Full grace: no payment (simplification - see README)
                    monthly_interest = 0
                    monthly_principal = 0
                    monthly_payment = 0
            else:
                # Regular month: fixed payment, split into interest + principal
                monthly_interest = balance * (annual_rate / 100 / 12)
                monthly_principal = payment_amount - monthly_interest
                monthly_payment = payment_amount

            balance -= monthly_principal
            balance = max(0, balance)  # guard against -0.00 from float rounding

            self.cursor.execute('''
                INSERT INTO PaymentSchedule
                (loan_id, month_number, payment_date, total_payment,
                 principal, interest, balance, is_grace_period)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (loan_id, month, payment_date.date().isoformat(), monthly_payment,
                  monthly_principal, monthly_interest, balance, is_grace))

            grace_text = "yes" if is_grace else "-"
            print(f"{month:<6} {str(payment_date.date()):<12} {monthly_payment:>11,.2f} "
                  f"{monthly_interest:>11,.2f} {monthly_principal:>11,.2f} "
                  f"{balance:>12,.2f} {grace_text:>6}")

        self.db.commit()
        print(f"\nSchedule for {borrower} calculated.")

    def show_summary(self, loan_id):
        """Summarise a loan with a single SQL query."""
        # LEFT JOIN (not JOIN): a loan with no schedule yet still appears, with
        # 0 payments. SUM() then returns NULL, which is displayed as 0.
        self.cursor.execute('''
            SELECT
                l.borrower,
                l.loan_amount,
                l.interest_rate,
                COUNT(p.payment_id) AS total_payments,
                SUM(p.interest)     AS total_interest,
                SUM(p.principal)    AS total_principal
            FROM Loans l
            LEFT JOIN PaymentSchedule p ON l.loan_id = p.loan_id
            WHERE l.loan_id = ?
            GROUP BY l.loan_id
        ''', (loan_id,))

        result = self.cursor.fetchone()

        if result:
            print(f"\n{'=' * 60}")
            print("Loan summary")
            print(f"{'=' * 60}")
            print(f"Borrower:            {result['borrower']}")
            print(f"Principal:           {result['loan_amount']:,.2f} ILS")
            print(f"Annual rate:         {result['interest_rate']}%")
            print(f"Number of payments:  {result['total_payments']}")
            print(f"Total interest paid: {result['total_interest'] or 0:,.2f} ILS")
            print(f"Total principal:     {result['total_principal'] or 0:,.2f} ILS")
            print(f"{'=' * 60}\n")


# Example usage
if __name__ == '__main__':
    calculator = AmortizationCalculator('loans.db')

    # Example 1: business loan with interest and a 6-month partial grace period
    print("\nExample 1: business loan with interest and partial grace")
    calculator.add_loan(
        loan_id=1,
        borrower='Israel Israeli',
        loan_amount=100000,
        interest_rate=5.00,
        loan_term_months=48,
        grace_period_months=6,
        grace_type='partial'
    )
    calculator.generate_payment_schedule(1)
    calculator.show_summary(1)

    # Example 2: interest-free loan
    print("\nExample 2: interest-free loan")
    calculator.add_loan(
        loan_id=2,
        borrower='Sarah Cohen',
        loan_amount=30000,
        interest_rate=0.00,
        loan_term_months=30,
        grace_period_months=0,
        grace_type='none'
    )
    calculator.generate_payment_schedule(2)
    calculator.show_summary(2)

    calculator.db.close()
