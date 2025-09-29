package dreamaware.videogen.egress

default allow := false

spiffe := input.attributes.source.principal
host := input.attributes.request.http.host
method := input.attributes.request.http.method
path := input.attributes.request.http.path

allowed := {
    "script_generation": {"api.openai.com","api.anthropic.com","api.deepseek.com","api.moonshot.cn"},
    "material_sourcing": {"api.pexels.com","pixabay.com"},
    "voice_synthesis": {"speech.platform.bing.com","api.openai.com","cognitiveservices.azure.com"}
}

purpose := "script_generation" { contains(spiffe, "/sa/llm-service") }
purpose := "material_sourcing" { contains(spiffe, "/sa/materials-service") }
purpose := "voice_synthesis" { contains(spiffe, "/sa/voice-service") }

# Budget check via header
within_budget {
    some id
    id := input.attributes.request.http.headers["x-job-id"]
    cost := data.crdb.jobs[id].actual_cost_usd
    cost < 5.0
}

allow {
    some p
    p := purpose
    host_allowed := host_in_set(host, allowed[p])
    host_allowed
    within_budget
}

host_in_set(h, set) {
    some v
    v := set[_]
    contains(h, v)
}
