def update_elo(r_a: float, r_b: float, result_a: float, k: int = 32) -> tuple[float,float]:
    # result_a: 1 win, 0 loss, 0.5 draw
    exp_a = 1.0 / (1.0 + 10 ** ((r_b - r_a) / 400.0))
    exp_b = 1.0 - exp_a
    r_a2 = r_a + k * (result_a - exp_a)
    r_b2 = r_b + k * ((1.0 - result_a) - exp_b)
    return r_a2, r_b2