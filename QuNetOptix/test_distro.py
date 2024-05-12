from vl_topo import CustomDoubleStarTopology 
from config import Config, Job
from typing import List
from vlaware_qnode import Transmit
from metadata import SimData, DistroResult
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
        te=200,
        acc=1000000,
        topo=CustomDoubleStarTopology(),
        vlinks=[('n2', 'n9')],
    )

@pytest.fixture
def oracle():
    return NetworkOracle()

@pytest.mark.parametrize('job', [
    ('n0', 'n2'), # physical one hop
    ('n0', 'n1'), # physical two hops
    ('n0', 'n5'), # physical two hops
])
def test_physical_sessions(oracle: NetworkOracle, config: Config, job):
    config.job = Job.custom(sessions=[job])
    config.schedule_n_vlinks=0
    config.continuous_distro=False

    meta_data: SimData = oracle.run(config)

    for transmit_id, distro_result in meta_data.distro_results.items():
        result_assertions(transmit_id, distro_result)

    assert meta_data.send_count == meta_data.success_count
    assert meta_data.remaining_mem_usage == 0

@pytest.mark.parametrize('job', [
    ('n0', 'n11'), # general forward
    ('n11', 'n0'), # general backward

    ('n2', 'n11'), # vlink start forward
    ('n9', 'n0'), # vlink start backward
    ('n0', 'n9'), # vlink end forward
    ('n11', 'n2'), # vlink end backward

    ('n2', 'n9'), # vlink only forward
    ('n9', 'n2'), # vlink only backward
])
def test_isolated_sessions(oracle: NetworkOracle, config: Config, job):
    config.job = Job.custom(sessions=[job])
    config.continuous_distro=False
    config.schedule_n_vlinks=1

    meta_data: SimData = oracle.run(config)

    for transmit_id, distro_result in meta_data.distro_results.items():
        result_assertions(transmit_id, distro_result)

    assert meta_data.send_count == meta_data.success_count
    assert meta_data.remaining_mem_usage == 0

@pytest.mark.parametrize('distro_send_rate', [1, 5, 10])
@pytest.mark.parametrize('vlink_send_rate', [1, 5, 10])
@pytest.mark.parametrize('sessions', [
    [
        # no overlay parallel
        ('n1', 'n10'), 
        ('n0', 'n11')
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
        # multiple same
        ('n0', 'n11'),
        ('n0', 'n11'),
        ('n0', 'n11'),

        ('n10', 'n1'),
        ('n10', 'n1'),
        ('n10', 'n1'),
    ],
])
def test_parallel_sessions(oracle: NetworkOracle, config: Config, sessions, vlink_send_rate, distro_send_rate):
    config.job = Job.custom(sessions=sessions)
    config.vlink_send_rate = vlink_send_rate
    config.send_rate = distro_send_rate
    config.continuous_distro=False
    config.schedule_n_vlinks=len(sessions)

    meta_data: SimData = oracle.run(config)

    for transmit_id, distro_result in meta_data.distro_results.items():
        result_assertions(transmit_id, distro_result)
    assert meta_data.send_count == meta_data.success_count
    assert meta_data.remaining_mem_usage == 0

def test_max_congestion(oracle: NetworkOracle, config: Config):
    sessions = [(f'n{i}', f'n{j}') for i in range(5) for j in range(7, 12) if i != j]
    sessions += [(f'n{i}', f'n{j}') for i in range(7, 12) for j in range(5) if i != j]

    config.te = 500
    config.job = Job.custom(sessions=sessions)
    config.topo = CustomDoubleStarTopology(memory_args=[{'capacity': 500}])
    config.vlink_send_rate = 20
    config.send_rate = 2
    config.continuous_distro=False
    config.schedule_n_vlinks=len(sessions)

    meta_data: SimData = oracle.run(config)

    for transmit_id, distro_result in meta_data.distro_results.items():
        result_assertions(transmit_id, distro_result)
    assert meta_data.send_count == meta_data.success_count
    assert meta_data.remaining_mem_usage == 0


@pytest.mark.parametrize('send_rate', [5, 10, 20])
@pytest.mark.parametrize('vlink_send_rate', [5, 10, 20])
@pytest.mark.parametrize('sessions_count', range(1, 7))
def test_random_continuous_requests(oracle, config, send_rate, vlink_send_rate, sessions_count):
    config.te = 50
    config.job = Job.random(session_count=sessions_count)
    config.send_rate = send_rate
    config.vlink_send_rate = vlink_send_rate
    config.continuous_distro = True

    meta_data: SimData = oracle.run(config)
    for transmit_id, distro_result in meta_data.distro_results.items():
        result_assertions(transmit_id, distro_result)

# TODO test revoke
# TODO test waxman topology
# TODO custom vlink (n2, n9)

