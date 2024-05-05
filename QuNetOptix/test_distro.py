from vl_topo import CustomDoubleStarTopology 
from config import Config, Job
from typing import List
from vlaware_qnode import Transmit
from metadata import MetaData, DistroResult
from qns.models.core import QuantumModel
from oracle import NetworkOracle

import pytest
import signal
import time
import multiprocessing

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
        te=50,
        acc=1000000,
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


@pytest.mark.parametrize('send_rate', [0.5, 5, 10])
@pytest.mark.parametrize('vlink_send_rate', [0.5, 5, 10])
@pytest.mark.parametrize('job', test_sessions)
def test_isolated_sessions(oracle, config, send_rate, vlink_send_rate, job):
    config.job = Job.custom(sessions=[job])
    config.send_rate = send_rate
    config.vlink_send_rate = vlink_send_rate
    meta_data: MetaData = oracle.run(config, continuous=False, monitor=False)

    assert meta_data.send_count == meta_data.success_count
    for transmit_id, distro_result in meta_data.distro_results.items():
        result_assertions(transmit_id, distro_result)
        # TODO: Add assertions for remaining mem usage

@pytest.mark.parametrize('sessions', [
    [
        # no overlay parallel
        ('n2', 'n11'), 
        ('n1', 'n3'), 
        ('n8', 'n7'),
    ],
    [
        # overlay forwards source overlay
        ('n0', 'n11'),
        ('n0', 'n10'),
        ('n0', 'n9'),
        ('n0', 'n8'),
        ('n0', 'n7')
    ],
    [
        # overlay forwards destination overlay
        ('n0', 'n11'),
        ('n1', 'n11'),
        ('n2', 'n11'),
        ('n3', 'n11'),
        ('n4', 'n11')
    ],
    [
        # overlay backwards source overlay
        ('n11', 'n0'),
        ('n11', 'n1'),
        ('n11', 'n2'),
        ('n11', 'n3'),
        ('n11', 'n4'),
    ],
    [
        # overlay backwards destination overlay
        ('n11', 'n0'),
        ('n10', 'n0'),
        ('n9', 'n0'),
        ('n8', 'n0'),
        ('n7', 'n0'),
    ],
    [
        # overlay forwards and backwards
        ('n0', 'n11'),
        ('n0', 'n10'),
        ('n11', 'n0'),
        ('n10', 'n0')
    ],
    [
        # overlay forwards and backwards vlink only
        ('n2', 'n9'),
        ('n9', 'n2'),
    ],
    [
        # misc
        ('n0', 'n11'), # forward vlink
        ('n0', 'n3'), # overlay src with previous session

        ('n9', 'n2'), # backward vlink only
        ('n11', 'n2'), # backward vlink and overlay dst with previous

        ('n8', 'n7'), # physical
    ],
])
def test_parallel_sessions(oracle, config, sessions):
    config.job = Job.custom(sessions=sessions)
    config.send_rate = 2
    config.vlink_send_rate = 2
    meta_data: MetaData = oracle.run(config, monitor=False)
    for transmit_id, distro_result in meta_data.distro_results.items():
        result_assertions(transmit_id, distro_result)

#def test_mem_clearance(oracle, config):
    #config.

# TODO
def test_random_requests(oracle, config):
    pass


