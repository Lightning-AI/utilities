import pytest

from lightning_utilities.core.rank_zero import rank_prefixed_message, rank_zero_only


@pytest.mark.parametrize("rank", [0, 1, 4])
def test_rank_prefixed_message(rank):
    rank_zero_only.rank = rank
    message = rank_prefixed_message("bar", rank)
    assert message == f"[rank: {rank}] bar"

    # reset
    rank_zero_only.rank = None
