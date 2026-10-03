from bridge.models import Hand
from bridge.opening_profile_policy import OpeningProfile, evaluate_two_suited_opening

HANDS = {
    988: "JT753.K9742.6.AT",
    1534: "T9843.AKJ32.7.65",
    6641: "J9643.QJ972.94.A",
    6900: "J9873.J9864.K.K7",
    9714: "Q8752.KT952.Q7.J",
    3220: "KQ653.J7432.97.K",
    4949: "AQ987.QJ974.-.862",
    6973: "KT876.KJ984.-.Q54",
    9577: "AK632.JT865.J.T6",
}

for profile in OpeningProfile:
    print(f"\n{profile.value}")
    for seed, hand_text in HANDS.items():
        hand = Hand.parse(hand_text)
        x = evaluate_two_suited_opening(hand, profile=profile, seat_number=3)
        print(seed, hand_text, x.hcp, x.rule20_score, x.status.value, x.call or "-")
