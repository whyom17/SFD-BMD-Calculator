import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, send_file, url_for
import io
import os

app = Flask(__name__)

# Helper function to calculate triangular load
def triangular_load(w_start, w_end, x_start, x_end):
    area = 0.5 * (w_start + w_end) * (x_end - x_start)
    x_bar = x_start + (x_end - x_start) * (2/3 if w_end > w_start else 1/3)
    return area, x_bar

@app.route('/', methods=['GET', 'POST'], endpoint= 'index')
def index():
    if request.method == 'POST':
        # Extract input data from the form
        L = float(request.form['beam_length'])
        P = float(request.form['pl_mag'])
        a = float(request.form['pl_pos'])
        w_udl = float(request.form['udl_mag'])
        x1_udl = float(request.form['udl_sp'])
        x2_udl = float(request.form['udl_ep'])
        w1_uvl = float(request.form['uvl1_mag_sp'])
        w2_uvl = float(request.form['uvl1_mag_ep'])
        x1_uvl = float(request.form['uvl1_sp'])
        x2_uvl = float(request.form['uvl1_ep'])
        w3_uvl = float(request.form['uvl2_mag_sp'])
        w4_uvl = float(request.form['uvl2_mag_ep'])
        x3_uvl = float(request.form['uvl2_sp'])
        x4_uvl = float(request.form['uvl2_ep'])

        # Calculate support reactions and shear & bending moment diagrams
        R1 = P * (L - a) / L
        R2 = P * a / L
        
        W_udl = w_udl * (x2_udl - x1_udl)
        x_udl = (x1_udl + x2_udl) / 2

        W_uvl1, x_uvl1 = triangular_load(w1_uvl, w2_uvl, x1_uvl, x2_uvl)
        W_uvl2, x_uvl2 = triangular_load(w3_uvl, w4_uvl, x3_uvl, x4_uvl)

        total_load = P + W_udl + W_uvl1 + W_uvl2

        moment_A = P * a + W_udl * x_udl + W_uvl1 * x_uvl1 + W_uvl2 * x_uvl2
        RB = moment_A / L
        RA = total_load - RB

        # Create SFD and BMD
        x_vals = np.linspace(0, L, 500)
        V = np.zeros_like(x_vals)
        M = np.zeros_like(x_vals)

        for i, x in enumerate(x_vals):
            V[i] += RA
            M[i] += RA * x

            if x >= a:
                V[i] -= P
                M[i] -= P * (x - a)

            if x >= x1_udl:
                length = min(x, x2_udl) - x1_udl
                if length > 0:
                    load = w_udl * length
                    centroid = x1_udl + length / 2
                    V[i] -= load
                    M[i] -= load * (x - centroid)

            if x >= x1_uvl:
                length = min(x, x2_uvl) - x1_uvl
                if length > 0:
                    eff_load, eff_pos = triangular_load(w1_uvl, w2_uvl, x1_uvl, x1_uvl + length)
                    V[i] -= eff_load
                    M[i] -= eff_load * (x - eff_pos)

            if x >= x3_uvl:
                length = min(x, x4_uvl) - x3_uvl
                if length > 0:
                    eff_load, eff_pos = triangular_load(w3_uvl, w4_uvl, x3_uvl, x3_uvl + length)
                    V[i] -= eff_load
                    M[i] -= eff_load * (x - eff_pos)

        # Plotting
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6))

        # Shear Force Diagram
        ax1.plot(x_vals, V, label="Shear Force", color='b')
        ax1.axhline(0, color='black', linewidth=0.8)
        ax1.set_title("Shear Force Diagram")
        ax1.set_xlabel("Position along Beam (m)")
        ax1.set_ylabel("Shear Force (N)")
        ax1.grid(True)
        ax1.legend()

        # Bending Moment Diagram
        ax2.plot(x_vals, M, label="Bending Moment", color='g')
        ax2.axhline(0, color='black', linewidth=0.8)
        ax2.set_title("Bending Moment Diagram")
        ax2.set_xlabel("Position along Beam (m)")
        ax2.set_ylabel("Bending Moment (Nm)")
        ax2.grid(True)
        ax2.legend()

        plt.tight_layout()

        # Perform calculations and create the plot as before...
        # After generating the plot, save it to a BytesIO object
        img_io = io.BytesIO()
        plt.savefig(img_io, format='png')
        img_io.seek(0)

        # You can save the file in a specific location, e.g., static folder
        img_path = os.path.join('static', 'beam_analysis_graph.png')
        with open(img_path, 'wb') as f:
            f.write(img_io.read())

        # Return the template with the URL of the image
        return render_template('index.html', graph_url=url_for('static', filename='beam_analysis_graph.png'))
    # If the request is GET, render the input form
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
