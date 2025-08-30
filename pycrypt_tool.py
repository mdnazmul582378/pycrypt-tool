import os
from flask import Flask, request, render_template_string, jsonify
from pycrypt import encode_code, decode_code
import marshal

# Initialize the Flask application
app = Flask(__name__)

# HTML template for the web interface, included as a string
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pycrypt Tool</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
        body {
            font-family: 'Inter', sans-serif;
            background-color: #1a202c;
            color: #e2e8f0;
        }
        textarea, input[type="file"] {
            background-color: #2d3748;
            border: 1px solid #4a5568;
            color: #e2e8f0;
        }
        .container {
            max-width: 800px;
        }
    </style>
</head>
<body class="bg-gray-900 text-gray-100 flex items-center justify-center min-h-screen p-4">
    <div class="container mx-auto p-6 bg-gray-800 rounded-xl shadow-lg border border-gray-700">
        <h1 class="text-3xl md:text-4xl font-bold text-center mb-6 text-indigo-400">Code Encrypter/Decrypter</h1>
        <p class="text-center text-gray-400 mb-8">Paste your code or upload a file to encode or decode.</p>

        <div class="mb-6">
            <label for="code-input" class="block text-sm font-medium mb-2 text-gray-300">Input Code/File</label>
            <textarea id="code-input" rows="10" placeholder="Paste your Python code here..." class="w-full p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition duration-300"></textarea>
            <p class="text-center text-gray-500 my-4">OR</p>
            <label for="file-input" class="w-full text-center block bg-gray-700 hover:bg-gray-600 cursor-pointer p-3 rounded-lg border border-dashed border-gray-500 transition duration-300">
                <span id="file-name">Click to select a .py file...</span>
                <input type="file" id="file-input" class="hidden" accept=".py">
            </label>
        </div>

        <div class="flex justify-center space-x-4 mb-6">
            <button id="encode-btn" class="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-md transition duration-300">Encode</button>
            <button id="decode-btn" class="px-6 py-3 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-lg shadow-md transition duration-300">Decode</button>
        </div>

        <div class="mb-6">
            <label for="code-output" class="block text-sm font-medium mb-2 text-gray-300">Output</label>
            <div class="relative">
                <textarea id="code-output" rows="10" readonly placeholder="Output will appear here..." class="w-full p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition duration-300"></textarea>
                <button id="copy-btn" class="absolute top-2 right-2 bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded-lg text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500 transition duration-300">Copy Code</button>
            </div>
        </div>

        <p id="status-message" class="text-center mt-4 text-sm text-gray-400"></p>
    </div>

    <script>
        const codeInput = document.getElementById('code-input');
        const fileInput = document.getElementById('file-input');
        const fileNameSpan = document.getElementById('file-name');
        const encodeBtn = document.getElementById('encode-btn');
        const decodeBtn = document.getElementById('decode-btn');
        const codeOutput = document.getElementById('code-output');
        const copyBtn = document.getElementById('copy-btn');
        const statusMessage = document.getElementById('status-message');

        fileInput.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                fileNameSpan.textContent = file.name;
                const reader = new FileReader();
                reader.onload = (e) => {
                    codeInput.value = e.target.result;
                    statusMessage.textContent = 'File loaded. You can now encode or decode.';
                };
                reader.readAsText(file);
            }
        });

        copyBtn.addEventListener('click', () => {
            codeOutput.select();
            codeOutput.setSelectionRange(0, 99999);
            document.execCommand('copy');
            statusMessage.textContent = 'Code copied to clipboard!';
        });

        encodeBtn.addEventListener('click', async () => {
            const code = codeInput.value.trim();
            if (code === '') {
                statusMessage.textContent = 'Please enter or upload code to encode.';
                return;
            }

            statusMessage.textContent = 'Encoding...';
            codeOutput.value = '';

            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'encode', code: code })
                });

                const result = await response.json();
                if (result.error) {
                    codeOutput.value = `Error: ${result.error}`;
                    statusMessage.textContent = 'Encoding failed.';
                } else {
                    const encoded_py_code = `import pycrypt,base64,zlib,marshal;encoded_data=b'${result.encoded_code}';compiled=pycrypt.decode_code(encoded_data);exec(compiled)`;
                    codeOutput.value = encoded_py_code;
                    statusMessage.textContent = 'Encoded successfully. Click "Copy Code" button.';
                }
            } catch (error) {
                statusMessage.textContent = 'An error occurred. Check the server logs.';
                console.error(error);
            }
        });

        decodeBtn.addEventListener('click', async () => {
            const code = codeInput.value.trim();
            if (code === '') {
                statusMessage.textContent = 'Please enter or upload code to decode.';
                return;
            }

            statusMessage.textContent = 'Decoding...';
            codeOutput.value = '';

            try {
                const encoded_data_match = code.match(/encoded_data=b'(.*?)'/s);
                if (!encoded_data_match || encoded_data_match.length < 2) {
                    statusMessage.textContent = 'Invalid encoded file format. Please provide a file encoded by this tool.';
                    return;
                }

                const encoded_data = encoded_data_match[1];

                const response = await fetch('/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'decode', code: encoded_data })
                });

                const result = await response.json();
                if (result.error) {
                    codeOutput.value = `Error: ${result.error}`;
                    statusMessage.textContent = 'Decoding failed.';
                } else {
                    codeOutput.value = result.decoded_code;
                    statusMessage.textContent = 'Decoded successfully.';
                }
            } catch (error) {
                statusMessage.textContent = 'An error occurred. Check the server logs.';
                console.error(error);
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """Serves the main HTML page."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process_code():
    """Handles the encoding and decoding requests."""
    data = request.json
    action = data.get('action')
    code_content = data.get('code')

    if not code_content:
        return jsonify({'error': 'No code provided.'}), 400

    if action == 'encode':
        encoded_data = encode_code(code_content)
        return jsonify({'encoded_code': encoded_data})
    elif action == 'decode':
        compiled_code = decode_code(code_content)
        if isinstance(compiled_code, str):
            return jsonify({'error': compiled_code}), 500
        
        # NOTE: Decoding a compiled object back to readable source code is not possible.
        # This message explains that limitation to the user.
        return jsonify({'decoded_code': 'Decoding successful. However, the original source code cannot be recovered directly from the compiled object. You can only execute it.'})
    else:
        return jsonify({'error': 'Invalid action.'}), 400

if __name__ == '__main__':
    from socket import gethostbyname, gethostname
    host_ip = gethostbyname(gethostname())
    port = 8000
    print(f"Server running. Visit http://{host_ip}:{port} in your browser.")
    app.run(host='0.0.0.0', port=port)