from flask import Flask, render_template, request, jsonify
from qiskit_aer import Aer
from qiskit_algorithms import Grover, AmplificationProblem
from qiskit.circuit.library import PhaseOracle
from qiskit.primitives import Sampler
from flask_cors import CORS
from flask_sock import Sock

app = Flask(__name__)
CORS(app) 
sock = Sock(app)  


motion_data = {
    'tremor': False,
    'jerk': False
}
detection_active = False


connected_clients = set()

@sock.route('/ws')
def handle_websocket(ws):
    connected_clients.add(ws)
    try:
        while True:
            data = ws.receive()
           
            for client in connected_clients:
                try:
                    client.send(data)
                except Exception:
                    connected_clients.remove(client)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connected_clients.remove(ws)

def sickness_lookup(code):
    sickness_dict = {
        '00000': 'Patient Healthy',
        '00001': 'Influenza',
        '00010': 'Allergic Reaction',
        '00011': 'Small Pox',
        '00100': 'Insomniac',
        '00101': 'Rabies',
        '00110': 'Plague',
        '00111': 'Typhoid',
        '01000': 'Active Tremor',
        '01001': 'Malaria',
        '01010': 'Lupus',
        '01011': 'West Nile Virus or Zika',
        '01100': 'Parkinson',
        '01101': 'Hyperthyroidism',
        '01110': 'Late Stage AIDs',
        '01111': 'DRESS Syndrome (Drug Reaction)',
        '10000': 'Myoclonus',
        '10001': 'Bacterial Meningitis',
        '10010': 'Multiple Sclerosis',
        '10011': 'Spotted Fever',
        '10100': 'Creutzfeldt-Jakob Disease',
        '10101': 'Serotonin Syndrome',
        '10110': 'Stevens Johnsons Syndrome',
        '10111': 'Neurotoxic Drug Reaction',
        '11000': 'Progressive Myoclonic Epilepsies',
        '11001': 'Mitochondrial Disorder',
        '11010': 'Heavy Metal Poisoning',
        '11011': 'Acute HIV',
        '11100': 'Restless Legs Syndrome',
        '11101': 'Thyrotoxic Crisis',
        '11110': 'MDMA Overdose',
        '11111': 'Acute Disseminated Encephalomyelitis'
    }
    return sickness_dict.get(code, 'Nothing Found')

def run_quantum_diagnosis(symptoms):
    log_expr = '('
    for i, symptom in enumerate(symptoms):
        if i > 0:
            log_expr += ' & '
        if symptom == '0':
            log_expr += f'~{["fever", "rash", "insomnia", "tremors", "jerks"][i]}'
        else:
            log_expr += f'{["fever", "rash", "insomnia", "tremors", "jerks"][i]}'
    log_expr += ')'


    oracle = PhaseOracle(log_expr)
    problem = AmplificationProblem(oracle)


    backend = Aer.get_backend('qasm_simulator')
    sampler = Sampler()


    grover = Grover(sampler=sampler)
    result = grover.amplify(problem)


    histogram_data = result.circuit_results
    winning_states = []
    
    for histogram in histogram_data:
        max_value = max(histogram.values())
        states = [key for key, value in histogram.items() if value == max_value]
        winning_states.extend(states)

    final_result = sickness_lookup(winning_states[0])
    return final_result

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/motion', methods=['POST'])
def update_motion():
    global motion_data, detection_active
    if not detection_active:
        return jsonify({'error': 'Detection is not active'}), 400
        
    data = request.json
    motion_type = data.get('type')
    
    if motion_type == 'tremor':
        motion_data['tremor'] = True
    elif motion_type == 'jerk':
        motion_data['jerk'] = True
    elif motion_type == 'none':
        motion_data['tremor'] = False
        motion_data['jerk'] = False
    
    return jsonify({'status': 'success'})

@app.route('/detection', methods=['POST'])
def toggle_detection():
    global detection_active
    action = request.json.get('action')
    
    if action == 'start':
        detection_active = True
        return jsonify({'status': 'success', 'message': 'Detection started'})
    elif action == 'stop':
        detection_active = False
        return jsonify({'status': 'success', 'message': 'Detection stopped'})
    else:
        return jsonify({'error': 'Invalid action'}), 400

@app.route('/diagnose', methods=['POST'])
def diagnose():
    global detection_active
    if detection_active:
        return jsonify({'error': 'Please stop detection before getting diagnosis'}), 400
        
    symptoms = request.json.get('symptoms', [])
    if len(symptoms) != 5:
        return jsonify({'error': 'Please provide exactly 5 symptoms'}), 400
    
    try:
       
        symptoms[3] = '1' if motion_data['tremor'] else '0'
        symptoms[4] = '1' if motion_data['jerk'] else '0'
        
        diagnosis = run_quantum_diagnosis(symptoms)
        return jsonify({'diagnosis': diagnosis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 