# -*- coding: utf-8 -*-
#!/venv/bin python3

def generate_flows(flow_number):
    """
    Generate traffic flows and return them.

    - Traffic flow features are defined by 'flow_feature' function
    - Flow data are saved in ServiceDB by means of 'insert_one_doc' method of 'service_database' object

    :param flow_number: (int) number of flows in the network
    :return: none
    """

    # init variables
    flow_categories = ['data', 'video', 'voice']
    trust_levels = [1, 2, 3]
    app_type = [1, 2, 3]
    already_chosen_endpoints = []

    # Get hosts data from database
    network_hosts = network_database.retrieve_all_collection_elements('hosts')
    # Get hosts' names only
    host_names = []
    for element in network_hosts:
        host_names.append(str(element['_id']))
    host_names.sort()  # sort hostnames

    for i in range(1, flow_number + 1):
        # define current flow category
        category = random.choice(flow_categories)

        # define current flow priority
        if category == 'voice':
            priority = 1
        elif category == 'video':
            priority = 2
        else:
            priority = 3

        # define current flow application type
        app = random.choice(app_type)

        # define flow features based on its category and application type
        [bw, delay, jitter, loss, dscp] = flow_features(category, app)

        # define current flow level of trust
        trust = random.choice(trust_levels)

        # flow endpoints
        node1 = random.choice(host_names)
        while True:
            # Check if node1 was previously chosen as flow endpoint
            if node1 in already_chosen_endpoints:
                # if so, choose another endpoint
                node1 = random.choice(host_names)
            else:
                # if not, add it to already_chosen_endpoints list
                already_chosen_endpoints.append(node1)
                break
        node2 = random.choice(host_names)
        while True:
            # Check if node2 was previously chosen as flow endpoint
            if node2 in already_chosen_endpoints:
                # if so, choose another endpoint
                node2 = random.choice(host_names)
            else:
                # if not, add it to already_chosen_endpoints list
                already_chosen_endpoints.append(node2)
                break

        flow_record = {
            '_id': 'flow{}'.format(i),
            'node1': node1,
            'node2': node2,
            'bandwidth': bw,
            'delay': delay,
            'jitter': jitter,
            'loss': loss,
            'trust': trust,
            'dscp': dscp,
            'priority': priority,
            'type': category
        }

        # create new db entry with flow data in 'flows' collection
        service_database.insert_one_doc('flows', flow_record)

    # store created flows in flows.json file
    store_service_info_json('flows')

    def store_service_info_json(services):
        """
        Save service info in json form (see ./jsonDB folder).

        :param services: (str) = 'flows'   # To Be REMOVED
        :return: None
        """

    # Init services_json
    services_json = {}

    # Retrieve all services stored in serviceDB...
    services_list = service_database.retrieve_all_collection_elements(services)

    # ...process and put them in services_json
    for k in range(1, len(services_list)+1):
        services_json['{}{}'.format(services[:-1], k)] = services_list[k-1]

    # Write 'flows.json' in ./jsonDB folder
    with open('{}/{}.json'.format(JSON_DB_FOLDER, services), 'w') as fp:
        json.dump(services_json, fp, sort_keys=True, indent=4)


def flow_features(category, app):
    """
    IETF RFC4594 - APPENDIX I (Section 2.3)
    -------------------------------------------------------------------------------------
    | Service Class |                               |     Tolerance to      |           |
    |      Name     |    Traffic Characteristics    | Loss | Delay | Jitter |   DSCP    |
    |===============+===============================+======+=======+========|===========|
    |               | Fixed-size small packets,     | Very |  Very |  Very  |           |
    |   Telephony   | constant emission rate,       |  Low |  Low  |  Low   |     46    |
    |               | inelastic and low-rate flows  |      |       |        |           |
    |---------------+-------------------------------+------+-------+--------|-----------|
    | Multimedia    | Variable size packets,        |  Low |  Very |        |           |
    | Conferencing  | constant transmit interval,   |   -  |  Low  |  Low   |     29    |
    |               | rate adaptive, reacts to loss |Medium|       |        |           |
    |---------------+-------------------------------+------+-------+--------|-----------|
    | Real-Time     | RTP/UDP streams, inelastic,   | Low  |  Very |  Low   |           |
    | Interactive   | mostly variable rate          |      |  Low  |        |     40    |
    |---------------+-------------------------------+------+-------+--------|-----------|
    | Multimedia    | Variable size packets,        |Low - |Medium |  Yes   |           |
    | Streaming     | elastic with variable rate    |Medium|       |        |     24    |
    |---------------+-------------------------------+------+-------+--------|-----------|
    | Low-Latency   | Variable rate, bursty short-  | Low  | Low - |  Yes   |           |
    | Data          | lived elastic flows           |      | Medium|        |     20    |
    |---------------+-------------------------------+------+-------+--------|-----------|
    |High-Throughput| Variable rate, bursty long-   | Low  | Medium|  Yes   |           |
    | Data          | lived elastic flows           |      |- High |        |     12    |
    |---------------+-------------------------------+------+-------+--------|-----------|
    | Low-Priority  | Non-real-time and elastic     | High |  High |  Yes   |           |
    | Data          |                               |      |       |        |     8     |
    -------------------------------------------------------------------------------------

    See Also:
        - ITU.T Recommendation G.1010
        - End-to-End QoS Network Design: Quality of Service for Rich-Media & Cloud Network (Chapter 10) - Cisco
    """

    #  **** VOICE FEATURES ****
    # Telephony --> VoIP
    if category == 'voice':
        bw = '1M'  # low bandwidth - Between 20 and 320 Kbps per call, depending on sampling rate, codec, L2 overhead
        delay = '100ms'  # Very Low - One-Way end-to-end < 150ms
        jitter = '15ms'  # Very Low - peak-to-peak < 30ms
        loss = 'None'  # Very Low - < 1%
        dscp = 46

    #  **** MULTIMEDIA FEATURES ****
    # Real-Time Interactive --> Interactive Gaming
    elif category == 'video' and app == 1:
        bw = '20M'  # high bandwidth
        delay = '100ms'  # Very Low - < 200ms
        jitter = '25ms'  # Low - peak-to-peak < 50ms
        loss = 'None'  # Low - < 0.1%
        dscp = 40
    # Multimedia Conferencing --> Video Conferencing
    elif category == 'video' and app == 2:
        bw = '20M'  # high bandwidth
        delay = '100ms'  # Very Low - < 200ms
        jitter = '25ms'  # Low - peak-to-peak < 50ms
        loss = '1%'  # Low/Medium - <= 1%
        dscp = 29
    # Multimedia Streaming --> On Demand Video Streaming
    elif category == 'video' and app == 3:
        bw = '20M'  # high bandwidth
        delay = '200ms'  # Medium - < 400 ms
        jitter = '50ms'  # Tolerant
        loss = '1%'  # Low/Medium - <= 1%
        dscp = 24

    #  **** DATA FEATURES ****
    # Low-Latency Data --> Transactional Data e.g. ATM, e-commerce
    elif category == 'data' and app == 1:
        bw = '1M'  # low bandwidth
        delay = '1000ms'  # Low/Medium - < 2s
        jitter = '100ms'  # Tolerant - N.A.
        loss = '1%'  # Low
        dscp = 20
    # High-Throughput Data --> Bulk Data
    elif category == 'data' and app == 2:
        bw = '20M'  # high bandwidth
        delay = '8000ms'  # Medium/High - < 15s
        jitter = '100ms'  # Tolerant - N.A.
        loss = '2%'  # Low
        dscp = 12
    # Low-Priority Data
    elif category == 'data' and app == 3:
        bw = '10M'  # medium/high bandwidth
        delay = '10000ms'  # High
        jitter = '100ms'  # Tolerant
        loss = '5%'  # High
        dscp = 8

    return [bw, delay, jitter, loss, dscp]