// Kalaa Setu — SHOULD policy #3
// A touchpoint admin (school/CSC staff) can see only their own village's data.
// A seller can read their own ledger.

// -------------------------------------------------------------------------
// Seller reads their own ledger entries.
// -------------------------------------------------------------------------
permit (
    principal is Seller,
    action == Action::"viewLedger",
    resource is LedgerEntry
)
when {
    principal.seller_id == resource.seller_id
};

forbid (
    principal is Seller,
    action == Action::"viewLedger",
    resource is LedgerEntry
)
when {
    principal.seller_id != resource.seller_id
};

// -------------------------------------------------------------------------
// Touchpoint admin reads their own touchpoint's data.
// The action list is on one line so the mock parser can read it.
// -------------------------------------------------------------------------
permit (
    principal is TouchpointAdmin,
    action in [Action::"viewSellerData", Action::"viewListingData", Action::"viewLedgerData"],
    resource is Seller
)
when {
    principal.touchpoint_id == resource.touchpoint_id
};

permit (
    principal is TouchpointAdmin,
    action in [Action::"viewSellerData", Action::"viewListingData", Action::"viewLedgerData"],
    resource is Listing
)
when {
    principal.touchpoint_id == resource.touchpoint_id
};

permit (
    principal is TouchpointAdmin,
    action in [Action::"viewSellerData", Action::"viewListingData", Action::"viewLedgerData"],
    resource is LedgerEntry
)
when {
    principal.touchpoint_id == resource.touchpoint_id
};

forbid (
    principal is TouchpointAdmin,
    action in [Action::"viewSellerData", Action::"viewListingData", Action::"viewLedgerData"],
    resource is Seller
)
when {
    principal.touchpoint_id != resource.touchpoint_id
};

forbid (
    principal is TouchpointAdmin,
    action in [Action::"viewSellerData", Action::"viewListingData", Action::"viewLedgerData"],
    resource is Listing
)
when {
    principal.touchpoint_id != resource.touchpoint_id
};

forbid (
    principal is TouchpointAdmin,
    action in [Action::"viewSellerData", Action::"viewListingData", Action::"viewLedgerData"],
    resource is LedgerEntry
)
when {
    principal.touchpoint_id != resource.touchpoint_id
};
