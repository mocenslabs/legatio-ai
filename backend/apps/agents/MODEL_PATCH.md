# Add to Agent model (after owner field)

```python
organization = models.ForeignKey(
    "organizations.Organization",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="agents",
    help_text="Optional organization scope. Null = personal agent owned only by user.",
)
```

And in Meta.indexes:
```python
models.Index(fields=["organization"], name="idx_agent_organization"),
```
