from vl_topo import CustomDoubleStarTopology 
from config import Config, Job
from typing import List
from vlaware_qnode import Transmit
from metadata import MetaData, DistroResult
from qns.models.core import QuantumModel
from oracle import NetworkOracle

import pytest

def result_assertions(transmit_id: str, distro_result: DistroResult):
    src_result_transmit: Transmit = distro_result.src_result[0]
    src_result_epr: QuantumModel = distro_result.src_result[1]
    dst_result_transmit: Transmit = distro_result.dst_result[0]
    dst_result_epr: QuantumModel = distro_result.dst_result[1]

    assert src_result_transmit.charlie.locA == dst_result_transmit.alice.locA == src_result_transmit.src == dst_result_transmit.src == src_result_epr.account.locA == dst_result_epr.account.locA
    assert src_result_transmit.charlie.locB == dst_result_transmit.alice.locB == src_result_transmit.dst == dst_result_transmit.dst == src_result_epr.account.locB == dst_result_epr.account.locB

    assert transmit_id == src_result_transmit.id
    assert transmit_id == dst_result_transmit.id
    assert transmit_id == src_result_epr.account.transmit_id
    assert transmit_id == dst_result_epr.account.transmit_id

    assert src_result_epr.name == dst_result_epr.name

@pytest.fixture
def config() -> Config:
    return Config(
        ts=0,
        te=10,
        acc=1000000,
        send_rate=1,
        topo=CustomDoubleStarTopology()
    )

@pytest.fixture
def oracle():
    return NetworkOracle()

test_sessions: List[Job] = [
    ('n0', 'n1'), # physical two hops
    ('n0', 'n2'), # physical one hop

    ('n0', 'n11'), # general forward
    ('n11', 'n0'), # general backward

    ('n2', 'n11'), # vlink start forward
    ('n9', 'n0'), # vlink start backward
    ('n0', 'n9'), # vlink end forward
    ('n11', 'n2'), # vlink end backward

    ('n2', 'n9'), # vlink only forward
    ('n9', 'n2'), # vlink only backward
]


@pytest.mark.parametrize('job', test_sessions)
def test_single_requests(oracle, config, job):
    config.job = Job.custom(sessions=[job])
    meta_data: MetaData = oracle.run(config, continuous=False, monitor=False)
    transmit_id, distro_result = next(iter(meta_data.distro_results.items()))
    result_assertions(transmit_id, distro_result)

    # TODO test remaining mem usage

@pytest.mark.parametrize('job', test_sessions)
def test_single_continuous_requests(oracle, config, job):
    config.job = Job.custom(sessions=[job])
    meta_data: MetaData = oracle.run(config, monitor=False)
    for transmit_id, distro_result in meta_data.distro_results.items():
        result_assertions(transmit_id, distro_result)

def test_no_overlay_parallel(oracle, config):
    config.job = Job.custom(sessions=[
        ('n2', 'n11'), 
        ('n1', 'n3'), 
        ('n8', 'n7'),
    ])
    meta_data: MetaData = oracle.run(config, monitor=False)
    for transmit_id, distro_result in meta_data.distro_results.items():
        result_assertions(transmit_id, distro_result)

def test_parallel_requests(oracle, config):
    test_sessions_parallel: List[Job] = [
        ('n0', 'n11'), # forward vlink
        ('n0', 'n3'), # overlay src with previous session

        ('n9', 'n2'), # backward vlink only
        ('n11', 'n2'), # backward vlink and overlay dst with previous

        ('n8', 'n7'), # physical
    ]

    config.job = Job.custom(sessions=test_sessions_parallel)

    '''
    meta_data: MetaData = oracle.run(config, monitor=False)
    for transmit_id, distro_result in meta_data.distro_results.items():
        result_assertions(transmit_id, distro_result)
    '''

def test_random_requests(oracle, config):
    pass


