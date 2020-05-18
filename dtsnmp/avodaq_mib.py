import logging
from .poller import Poller
from .processing import process_metrics, reduce_average, split_oid_index

logger = logging.getLogger(__name__)


class AvodaqProcessMIB():
    """
	Metric processing for AVODAQ-METRICS

	Reference
	http://www.circitor.fr/Mibs/Html/C/CISCO-PROCESS-MIB.php

	Usage
	cisco_mib = CiscoProcessMIB(device, authentication)
	cisco_metrics = cisco_mib.poll_metrics()

	Returns a dictionary containing values for:
	CPU Utilsation
	Memory Utilisation
	"""

    mib_name = 'AVODAQ-METRICS'

    def __init__(self, device, authentication):
        self.poller = Poller(device, authentication)

    def poll_metrics(self):
        cpu = self._poll_cpu()
        mem_cpu = self._poll_memory()

        cpu_utilisation = cpu.get('cpu', [])
        memory_cpu = mem_cpu.get('memory_Processor', [])
        memory_io = mem_cpu.get('memory_I/O', [])

        metrics = {
            'cpu_utilisation': cpu_utilisation,
            'memory_utilisation_cpu': memory_cpu,
            'memory_utilisation_io': memory_io
        }
        return metrics

    def _poll_cpu(self):
        cpu_endpoints = [
            '1.3.6.1.4.1.9.9.109.1.1.1.1.7'  # cpmCPUTotal1minRev - CPU busy % for the last min
        ]
        gen = self.poller.snmp_connect_bulk(cpu_endpoints)
        return process_metrics(gen, calculate_cisco_cpu)

    def _poll_memory(self):
        memory_endpoints = [
            '1.3.6.1.4.1.9.9.48.1.1.1.2',  # cempMemPoolName - Mmmory Name #1
            '1.3.6.1.4.1.9.9.48.1.1.1.5',  # cempMemPoolUsed - Memory Used #1
            '1.3.6.1.4.1.9.9.48.1.1.1.6'  # cempMemPoolFree - Memory Free  #1
        ]
        gen = self.poller.snmp_connect_bulk(memory_endpoints)
        return process_metrics(gen, calculate_cisco_memory)

def calculate_cisco_cpu(varBinds, metrics):
    cpu = {}
    index = split_oid_index(varBinds[0][0])
    cpu['value'] = float(varBinds[0][1])
    cpu['dimension'] = {'Index': index}
    cpu['is_absolute_number'] = True
    metrics.setdefault('cpu', []).append(cpu)
    print('CPU calculated: ' + str(cpu['value']))
    return metrics

def calculate_cisco_memory(varBinds, metrics):
    memory_name = varBinds[0][1].prettyPrint()
    memory_used = float(varBinds[1][1])
    memory_free = float(varBinds[2][1])
    memory_total = memory_used + memory_free
    memory_utilisation = 0
    if memory_total > 0:
        memory_utilisation = (memory_used / memory_total) * 100
    memory = {}
    memory['value'] = memory_utilisation
    memory['dimension'] = {'Storage': memory_name}
    memory['is_absolute_number'] = True

    metrics.setdefault('memory_{}'.format(memory_name), []).append(memory)
    print('Memory calculated: ' + str(memory['value']))
    return metrics