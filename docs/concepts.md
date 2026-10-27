┌──────────┬──────────────────────────────────────────────────────────────┐
│ Problem  │ Customers have no self-service way to query shipment status  │
│          │ without calling support                                      │
├──────────┼──────────────────────────────────────────────────────────────┤
│ Users    │ Customers of SecureShip who have active shipments            │
├──────────┼──────────────────────────────────────────────────────────────┤
│ Success  │ Customer gets a correct, scoped answer about their own       │
│          │ shipment; no other customer's data is ever visible           │
├──────────┼──────────────────────────────────────────────────────────────┤
│ Data     │ Every query is filtered by authenticated customer ID in      │
│ rules    │ code, never by prompt instruction alone                      │
└──────────┴──────────────────────────────────────────────────────────────┘