// Kalaa Setu — MUST policy #1
// A seller can edit only their own listing.
//
// Principal: Seller (identified by seller_id)
// Action:    "editListing"
// Resource:  Listing (identified by listing_id, carrying its owning seller_id)
//
// Deny is the default in Cedar; this policy grants access only when the
// listing's owning seller_id matches the requesting principal's seller_id.

permit (
    principal is Seller,
    action == Action::"editListing",
    resource is Listing
)
when {
    principal.seller_id == resource.seller_id
};

// Explicit deny so that even if another policy is added later, a seller can
// never edit a listing that belongs to someone else. Deny always wins in Cedar.
forbid (
    principal is Seller,
    action == Action::"editListing",
    resource is Listing
)
when {
    principal.seller_id != resource.seller_id
};
