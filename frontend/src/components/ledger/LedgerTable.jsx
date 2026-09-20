import React from 'react';
import EmptyState from '../common/EmptyState';

export default function LedgerTable({ entries }) {
  if (!entries || entries.length === 0) {
    return <EmptyState title="No ledger entries yet">Simulate a sale to see entries appear here.</EmptyState>;
  }

  return (
    <div className="ledger-table-scroll">
      <table className="ledger-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Listing</th>
          <th>Sale amount</th>
          <th>Platform fee</th>
          <th>Your net</th>
          <th>Contribution</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((e) => (
          <tr key={e.ledger_entry_id}>
            <td>{new Date(e.created_at).toLocaleDateString('en-IN')}</td>
            <td>{e.listing_id}</td>
            <td>₹{e.sale_amount.toLocaleString('en-IN')}</td>
            <td>₹{e.platform_fee.toLocaleString('en-IN')}</td>
            <td>₹{e.seller_net.toLocaleString('en-IN')}</td>
            <td>{e.contribution_amount > 0 ? `₹${e.contribution_amount.toLocaleString('en-IN')}` : '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
    </div>
  );
}

