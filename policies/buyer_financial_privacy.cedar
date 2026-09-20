// Kalaa Setu — SHOULD policy #4
// A buyer cannot access private seller financial information.

forbid (
    principal is Buyer,
    action in [Action::"viewLedger", Action::"viewSellerNet", Action::"viewPlatformFee", Action::"viewContributionAmount"],
    resource is LedgerEntry
);

forbid (
    principal is Buyer,
    action in [Action::"viewLedger", Action::"viewSellerNet", Action::"viewPlatformFee", Action::"viewContributionAmount"],
    resource is Seller
);

permit (
    principal is Buyer,
    action == Action::"viewImpactAggregate",
    resource is ImpactAggregate
);
