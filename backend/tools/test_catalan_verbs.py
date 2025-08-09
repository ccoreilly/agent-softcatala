import pytest
from .catalan_verbs import CatalanVerbsTool

@pytest.fixture
def catalan_verbs_tool():
    return CatalanVerbsTool()

@pytest.mark.asyncio
async def test_search_conjugations(catalan_verbs_tool):
    result = await catalan_verbs_tool.execute(action="search", verb="anar")
    assert result is not None
    assert isinstance(result, list)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_autocomplete(catalan_verbs_tool):
    result = await catalan_verbs_tool.execute(action="autocomplete", verb="assumi")
    assert result is not None
    assert isinstance(result, list)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_index(catalan_verbs_tool):
    result = await catalan_verbs_tool.execute(action="index", verb="a")
    assert result is not None
    assert isinstance(result, list)
    assert len(result) > 0