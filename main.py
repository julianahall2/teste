import os
import numpy as np
import matplotlib.colors as mcolors
import scipy.ndimage as ndimage
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify, send_file
import pydicom

app = Flask(__name__)

def anonymize_dicom_file(input_path, output_directory):
    """
    Função para anonimizar um arquivo DICOM.

    Args:
        input_path (str): Caminho do arquivo DICOM de entrada.
        output_directory (str): Diretório de saída para o arquivo anonimizado.

    Returns:
        str: Caminho do arquivo DICOM anonimizado.
    """
def anonymize_dicom_file(input_path, output_directory):
    """
    Função para anonimizar um arquivo DICOM.

    Args:
        input_path (str): Caminho do arquivo DICOM de entrada.
        output_directory (str): Diretório de saída para o arquivo anonimizado.

    Returns:
        str: Caminho do arquivo DICOM anonimizado.
    """
    try:
        ds = pydicom.dcmread(input_path)
        ds.PatientName = "Paciente Anônimo"
        ds.PatientID = "ID Anônimo"
        
        output_path = os.path.join(output_directory, "anonimizado_" + os.path.basename(input_path))
        ds.save_as(output_path)
        
        return output_path

    except pydicom.errors.InvalidDicomError as e:
        return str(e)

@app.route('/anonimizar', methods=['POST'])
def anonimize_dicom():
    """
    Rota para anonimizar um arquivo DICOM.
    """
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo fornecido"})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nome de arquivo vazio"})

    output_directory = "ArquivosAnonimizados"
    os.makedirs(output_directory, exist_ok=True)
    input_path = os.path.join(output_directory, file.filename)

    file.save(input_path)
    anonymized_file = anonymize_dicom_file(input_path, output_directory)

    if isinstance(anonymized_file, str):
        return send_file(anonymized_file, as_attachment=True)
    else:
        return jsonify({"error": anonymized_file})

def preprocess_dicom(input_path, output_directory):
    """
    Função para pré-processamento de um arquivo DICOM.

    Args:
        input_path (str): Caminho do arquivo DICOM de entrada.
        output_directory (str): Diretório de saída para o arquivo pré-processado.
    
    Returns:
        str: Caminho do arquivo DICOM pré-processado.
    """
    try:
        ds = pydicom.dcmread(input_path)
        pixel_array = ds.pixel_array
        
        # Realize o pré-processamento aqui, como correção de contraste, remoção de ruído, equalização de histograma, etc.
        
        preprocessed_path = os.path.join(output_directory, "preprocessed_" + os.path.basename(input_path))
        ds.PixelData = pixel_array.tobytes()
        ds.save_as(preprocessed_path)
        
        return preprocessed_path
    except pydicom.errors.PydicomError as e:
        return str(e)

def segment_dicom(input_path, threshold):
    """
    Função para segmentar um arquivo DICOM.

    Args:
        input_path (str): Caminho do arquivo DICOM de entrada.
        threshold (int): Valor de limiar para segmentação.

    Returns:
        numpy.ndarray: Matriz segmentada.
    """
    try:
        ds = pydicom.dcmread(input_path)
        pixel_array = ds.pixel_array
        mask = np.where(pixel_array > threshold, 1, 0)

        # Realize a segmentação avançada, se necessário

        labeled_array, num_labels = ndimage.label(mask)
        unique_labels = np.unique(labeled_array)

        masked_slice = np.zeros_like(labeled_array, dtype=int)
        for label in unique_labels[1:]:
            masked_slice[labeled_array == label] = label

        return masked_slice

    except pydicom.errors.InvalidDicomError as e:
        return str(e)

        
@app.route('/segmentar', methods=['POST'])
def segmentar_dicom():
    """
    Rota para segmentar um arquivo DICOM.
    """
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo fornecido"})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nome de arquivo vazio"})

    output_directory = "ArquivosSegmentados"
    os.makedirs(output_directory, exist_ok=True)
    input_path = os.path.join(output_directory, "segmentado_" + file.filename)

    file.save(input_path)

    # Pré-processamento opcional
    preprocessed_file = preprocess_dicom(input_path, output_directory)

    if isinstance(preprocessed_file, str):
        # Threshold dinâmico (pode ser um valor escolhido pelo usuário)
        dynamic_threshold = 1000

        segmented_mask = segment_dicom(preprocessed_file, dynamic_threshold)

        # Create a custom colormap with different colors for each organ
        custom_colors = ['red', 'green', 'blue', 'orange', 'purple', 'pink', 'cyan', 'magenta', 'yellow', 'brown']
        custom_cmap = mcolors.ListedColormap(custom_colors)

        # Apply the mask to the organs and set the background to black
        masked_slice = np.ma.masked_where(segmented_mask == 0, segmented_mask)

        fig, ax = plt.subplots()
        cax = ax.imshow(masked_slice[20], cmap=custom_cmap, interpolation='nearest')

        # Add a custom legend for the organs
        cbar = plt.colorbar(cax, orientation='vertical', ticks=range(10))
        cbar.ax.set_yticklabels(['Orgão 0', 'Orgão 1', 'Orgão 2', 'Orgão 3', 'Orgão 4', 'Orgão 5', 'Orgão 6', 'Orgão 7', 'Orgão 8', 'Orgão 9'])

        plt.axis('off')
        plt.savefig('segmented_image.png')
        plt.close()

        image_path = os.path.join(output_directory, 'segmented_image.png')
        return send_file(image_path, as_attachment=True)
    else:
        return jsonify({"error": preprocessed_file})

def segment_3d_organ(input_directory, output_directory, organ_name, threshold):
    """
    Função para segmentar um órgão em um volume 3D de arquivos DICOM.

    Args:
        input_directory (str): Diretório de entrada contendo os arquivos DICOM.
        output_directory (str): Diretório de saída para o arquivo segmentado.
        organ_name (str): Nome do órgão a ser segmentado.
        threshold (int): Valor de limiar para segmentação.

    Returns:
        str: Caminho do arquivo DICOM segmentado.
    """
    try:
        # Obtenha uma lista de todos os arquivos DICOM no diretório de entrada
        dicom_files = [os.path.join(input_directory, filename) for filename in os.listdir(input_directory) if filename.endswith('.dcm')]

        if not dicom_files:
            return jsonify({"error": "Nenhum arquivo DICOM encontrado no diretório de entrada."})

        # Leia o primeiro arquivo DICOM para obter informações de dimensões
        first_ds = pydicom.dcmread(dicom_files[0])
        rows, cols, num_slices = first_ds.Rows, first_ds.Columns, len(dicom_files)

        # Crie um volume 3D para armazenar os dados
        volume = np.zeros((num_slices, rows, cols), dtype=np.uint16)

        # Leia todos os arquivos DICOM e preencha o volume 3D
        for i, dicom_file in enumerate(dicom_files):
            ds = pydicom.dcmread(dicom_file)
            volume[i, :, :] = ds.pixel_array

        # Realize a segmentação 3D (usando um limiar dinâmico, por exemplo)
        organ_volume = np.where(volume > threshold, 1, 0)

        # Salve o volume segmentado em DICOM ou outro formato, se necessário
        organ_ds = pydicom.Dataset()
        organ_ds.Rows = rows
        organ_ds.Columns = cols
        organ_ds.NumberOfFrames = num_slices
        organ_ds.PixelData = organ_volume.tobytes()
        organ_ds.save_as(os.path.join(output_directory, f"{organ_name}_segmented.dcm"))

        return os.path.join(output_directory, f"{organ_name}_segmented.dcm")

    except pydicom.errors.PydicomError as e:
        return str(e)

@app.route('/segmentar_3d', methods=['POST'])
def segmentar_3d_organ():
    """
    Rota para segmentar um órgão em um volume 3D de arquivos DICOM.
    """
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo fornecido"})

    file = request.files['file']
    if file.filename == '':
     return jsonify({"error": "Nome de arquivo vazio"})

    organ_name = request.form.get('organ_name')
    if not organ_name:
        return jsonify({"error": "Nome do órgão não fornecido"})

    output_directory = "ArquivosSegmentados3D"
    os.makedirs(output_directory, exist_ok=True)

    input_directory = os.path.join(output_directory, "input")
    os.makedirs(input_directory, exist_ok=True)

    file.save(os.path.join(input_directory, file.filename))

# Pré-processamento opcional
    preprocessed_directory = os.path.join(output_directory, "preprocessed")
    os.makedirs(preprocessed_directory, exist_ok=True)

    preprocessed_file = preprocess_dicom(os.path.join(input_directory, file.filename), preprocessed_directory)

    if isinstance(preprocessed_file, str):
    # Threshold dinâmico (pode ser um valor escolhido pelo usuário)
        dynamic_threshold = 1000

    segmented_3d_organ = segment_3d_organ(preprocessed_directory, output_directory, organ_name, dynamic_threshold)

    if isinstance(segmented_3d_organ, str):
        return send_file(segmented_3d_organ, as_attachment=True)
    else:
        return jsonify({"error": segmented_3d_organ})

if __name__ == '__main__':
    app.run(port=5430, host='localhost', debug=True)
