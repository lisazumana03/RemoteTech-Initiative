# RemoteTech — Roadmap to a Sellable Product by October

**Today:** 6 September 2026
**Target:** Ready to demo/sell by early October (~4 weeks)

This roadmap sequences the work from the feature review, ordered so the
riskiest/most sale-blocking items get fixed first. Each week ends with
something demoable.

---

## Week 1 (Sep 7 – Sep 13): Make it safe to run other people's code

The current `safe_exec` blocks a hardcoded list of substrings
(`"import os"`, `"__import__"`, etc.) which is trivial to bypass. This is
the top risk if you're hosting code execution for schools.

- [ ] Replace the substring blocklist with a restricted-builtins sandbox
      (whitelist safe builtins, strip `eval`, `exec`, `compile`, `open`,
      `__import__`, `getattr`/`setattr`, `globals`/`locals`)
- [ ] Add an execution timeout (prevents infinite loops from hanging the app)
- [ ] Add a memory/CPU resource limit where the OS supports it
- [ ] Move off local SQLite to a hosted Postgres instance (Supabase, Railway,
      or Render) — required before multiple schools touch the same deploy
- [ ] Deploy to a persistent host with a real domain (not local-only)

**Demo at end of week:** app runs on a real URL, backed by a real DB, and
survives someone trying to break the sandbox.

---

## Week 2 (Sep 14 – Sep 20): Make it usable by more than one class

- [ ] Add a `school` / `class` field to the user model
- [ ] Scope the admin dashboard, leaderboard, and CSV export to a class/school
- [ ] Add password-reset flow (currently a dead end if forgotten)
- [ ] Add a demo/trial account so prospects can try it without you creating
      real logins
- [ ] Basic rate-limiting or abuse protection on the code-run endpoint

**Demo at end of week:** two separate "schools" can use the same deployment
without seeing each other's students.

---

## Week 3 (Sep 21 – Sep 27): Make it worth paying for

- [ ] Add 2–3 more quest sets (dictionaries, simple mini-projects) so the
      content library isn't just 6 quests
- [ ] Move quest definitions out of hardcoded Python into a DB/JSON structure
      an admin can edit — this is what lets you resell without a code change
      per customer
- [ ] Add a lightweight Stripe checkout or license-key flow so you can
      actually invoice/charge a school
- [ ] Write down (even briefly) your data retention policy and hosting
      location — schools will ask this during procurement

**Demo at end of week:** a teacher can add a new quest without your help,
and there's a way to actually collect payment.

---

## Week 4 (Sep 28 – Oct 4): Polish that closes the deal

- [ ] Simple white-label option (logo/color swap per school)
- [ ] Parent/teacher progress email or shareable progress link
- [x] ~~isiXhosa/Afrikaans language toggle for at least the core UI strings~~ (dropped — out of scope, removed from codebase)
- [ ] One-page marketing/landing site separate from the app
- [ ] Full run-through as a brand-new user: register → quests → certificate →
      profile → delete account, fixing anything broken along the way

**Demo at end of week:** the version you'd actually put in front of a
buyer.

---

## Buffer (Oct 5 – Oct 11)

Keep this week unscheduled. Something in weeks 1–4 will slip — this is
where it lands, plus final bug fixes before any real sales conversations.

---

## Explicitly deferred (not needed for October)

These matter long-term but aren't blockers for a first sale — revisit
after you have a paying customer or two:
- Mobile app / native mobile experience
- Full accessibility audit
- Additional programming languages beyond Python
- Advanced analytics (engagement trends over time, cohort comparisons)
