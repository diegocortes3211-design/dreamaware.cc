package agent.permissions

test_allow_all_good {
  data.agent.permissions.allow with input as {"capabilities": ["network.access","storage.read"]}
}

test_deny_unlisted_capability {
  not data.agent.permissions.allow with input as {"capabilities": ["fs.root"]}
}

test_deny_empty_list {
  not data.agent.permissions.allow with input as {"capabilities": []}
}
