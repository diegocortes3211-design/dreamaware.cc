package dreamaware.videogen.input

default allow := false

valid_chars := `^[a-zA-Z0-9\s\.,!?\-'""]+$`

injection(s) {
    lower(s) =~ ".*(ignore previous|system:|<\\|im_start\\|>|\\[INST\\]).*"
}

allow {
    topic := input.body.topic
    count(topic) >= 3
    count(topic) <= 500
    not injection(topic)
    regex.match(valid_chars, topic)
}
