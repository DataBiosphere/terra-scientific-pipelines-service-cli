### Description 

_Please replace this description with a concise description of this Pull Request._

### Jira Ticket


### Checklist (provide links to changes)

- [ ] Test that auth flow still works, since this isn't covered by tests
    1. Main flow: run `terralab logout` and then `terralab pipelines list` - should prompt a browser login
    2. Refresh token flow: run `rm ~/.terralab/access_token` and then `terralab pipelines list` - should succeed without a browser login
- [ ] Updated external documentation (if applicable)
- [ ] Updated internal documentation (if applicable)
- [ ] Planned non patch version bump (if applicable)
- [ ] Updated Teaspoons PR (if applicable)
