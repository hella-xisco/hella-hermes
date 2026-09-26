"""A provider may reuse call_0 for a new call on every assistant turn."""
import copy
from types import SimpleNamespace

from run_agent import AIAgent


def call(cid='call_0', name='terminal'):
    return {'role': 'assistant', 'content': '', 'tool_calls': [
        {'id': cid, 'call_id': cid, 'response_item_id': 'fc_0',
         'type': 'function', 'function': {'name': name, 'arguments': '{}'}}]}


def result(text, cid='call_0'):
    return {'role': 'tool', 'tool_call_id': cid, 'content': text}


def assert_pairs(messages):
    calls = [AIAgent._get_tool_call_id_static(tc) for m in messages
             for tc in m.get('tool_calls', [])]
    results = [m['tool_call_id'] for m in messages if m['role'] == 'tool']
    assert len(calls) == len(set(calls))
    assert len(results) == len(set(results))
    assert calls == results
    assert not any(m.get('tool_calls') == [] for m in messages)


def test_reused_ids_keep_every_result_and_do_not_mutate_history():
    messages = [call(), result('initial tool'), call(name='youtube_transcript'),
                result('transcript one'), call(name='youtube_transcript'),
                result('transcript two'), call(), result('terminal output')]
    original = copy.deepcopy(messages)
    output = AIAgent._sanitize_api_messages(messages)
    assert [m['content'] for m in output if m['role'] == 'tool'] == [
        'initial tool', 'transcript one', 'transcript two', 'terminal output']
    assert_pairs(output)
    assert messages == original
    assert AIAgent._sanitize_api_messages(messages) == output
    assert AIAgent._sanitize_api_messages(output) == output
    # Appending another provider response must not churn the cached prefix.
    extended = AIAgent._sanitize_api_messages(messages + [call(), result('new')])
    assert extended[:len(output)] == output
    for m in output:
        for tc in m.get('tool_calls', []):
            assert tc['id'] == tc['call_id']


def test_missing_result_is_stubbed_for_the_correct_occurrence():
    output = AIAgent._sanitize_api_messages([call(), result('old'), call()])
    assert_pairs(output)
    results = [m['content'] for m in output if m['role'] == 'tool']
    assert results[0] == 'old'
    assert 'unavailable' in results[1]


def test_duplicate_results_without_new_calls_are_still_removed():
    second = call()
    second['tool_calls'] *= 2
    output = AIAgent._sanitize_api_messages([
        call(), result('first'), result('duplicate first'),
        second, result('second'), result('duplicate second')])
    assert_pairs(output)
    assert [m['content'] for m in output if m['role'] == 'tool'] == ['first', 'second']


def test_sdk_objects_are_copied_and_paired():
    tc = SimpleNamespace(id='call_0', call_id='call_0', response_item_id='fc_0',
                         function=SimpleNamespace(name='terminal', arguments='{}'))
    messages = [call(), result('one'), {'role': 'assistant', 'tool_calls': [tc]}, result('two')]
    output = AIAgent._sanitize_api_messages(messages)
    assert_pairs(output)
    assert tc.id == tc.call_id == 'call_0'
    remapped = output[2]['tool_calls'][0]
    assert remapped.id == remapped.call_id != tc.id


def test_parallel_call_results_keep_their_own_pairings():
    first, second = call(), call()
    first['tool_calls'].append(call('call_1')['tool_calls'][0])
    second['tool_calls'].append(call('call_1')['tool_calls'][0])
    output = AIAgent._sanitize_api_messages([
        first, result('a0'), result('a1', 'call_1'),
        second, result('b1', 'call_1'), result('b0')])
    mapping = {m['tool_call_id']: m['content'] for m in output if m['role'] == 'tool'}
    calls = [m['tool_calls'] for m in output if m['role'] == 'assistant']
    assert [mapping[tc['id']] for batch in calls for tc in batch] == ['a0', 'a1', 'b0', 'b1']


def test_provider_ids_colliding_with_generated_ids_remain_unique():
    prefix = [call(), result('first'), call(), result('second')]
    before = AIAgent._sanitize_api_messages(prefix)
    generated = before[2]['tool_calls'][0]['id']
    output = AIAgent._sanitize_api_messages(prefix + [call(generated), result('third', generated)])
    assert output[:len(before)] == before
    assert_pairs(output)
    assert [m['content'] for m in output if m['role'] == 'tool'] == ['first', 'second', 'third']
