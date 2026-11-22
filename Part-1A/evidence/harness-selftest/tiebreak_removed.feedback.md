# Harness feedback — run-001 (FAIL)

Label: SELF-TEST mutant: tiebreak_removed

| Gate | Result | Exit |
|------|--------|------|
| integrity | PASS | 0 |
| lint | PASS | 0 |
| security | PASS | 0 |
| tests | FAIL | 1 |

## Failed tests (2)

### tests.contract.test_cli_list::test_as3_2_priority_sort_with_tiebreakers

- kind: failure
- message: assert [2, 4, 5, 3, 1] == [4, 5, 2, 3, 1]
  
  At index 0 diff: 2 != 4
  Use -v to get more diff

```text
cli = <tests.conftest.Cli object at 0x10ac18c20>

    def test_as3_2_priority_sort_with_tiebreakers(cli):
        seed_priorities(cli)
        r = cli("list", "--sort", "priority")
        # high: 4 (10:01, id4), 5 (10:01, id5), 2 (10:05); medium: 3; low: 1
>       assert ids(r.out) == [4, 5, 2, 3, 1]
E       assert [2, 4, 5, 3, 1] == [4, 5, 2, 3, 1]
E         
E         At index 0 diff: 2 != 4
E         Use -v to get more diff

tests/contract/test_cli_list.py:40: AssertionError
```

### tests.contract.test_cli_list::test_as3_5_json_output

- kind: failure
- message: assert [2, 4, 5, 3, 1] == [4, 5, 2, 3, 1]
  
  At index 0 diff: 2 != 4
  Use -v to get more diff

```text
cli = <tests.conftest.Cli object at 0x10acd2f30>

    def test_as3_5_json_output(cli):
        seed_priorities(cli)
        r = cli("list", "--json", "--sort", "priority")
        data = json.loads(r.out)
>       assert [t["id"] for t in data] == [4, 5, 2, 3, 1]
E       assert [2, 4, 5, 3, 1] == [4, 5, 2, 3, 1]
E         
E         At index 0 diff: 2 != 4
E         Use -v to get more diff

tests/contract/test_cli_list.py:82: AssertionError
```

Instructions to the coding agent: repair `src/` only. Do not edit tests, the spec, or anything under `.harness/` (integrity gate).
