// Kalaa Setu — MUST policy #2
// A community contribution can be routed only if the seller has explicitly opted in.

// -------------------------------------------------------------------------
// Rule A: a seller may SET their own contribution record.
// The principal must be the same seller as the resource.
// -------------------------------------------------------------------------
permit (
    principal is Seller,
    action == Action::"setContribution",
    resource is Contribution
)
when {
    principal.seller_id == resource.seller_id
};

// A seller may NEVER set another seller's contribution record.
forbid (
    principal is Seller,
    action == Action::"setContribution",
    resource is Contribution
)
when {
    principal.seller_id != resource.seller_id
};

// -------------------------------------------------------------------------
// Rule B: a contribution may only be ROUTED if the seller has opted in.
// -------------------------------------------------------------------------
permit (
    principal is Seller,
    action == Action::"routeContribution",
    resource is Contribution
)
when {
    resource.opted_in == true
};

forbid (
    principal is Seller,
    action == Action::"routeContribution",
    resource is Contribution
)
when {
    resource.opted_in == false
};

forbid (
    principal is Seller,
    action == Action::"routeContribution",
    resource is Contribution
)
when {
    resource.percentage < 0 || resource.percentage > 100
};
