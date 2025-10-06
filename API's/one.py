from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory "database"
employees = []

# GET all employees
@app.route('/employees', methods=['GET'])
def get_employees():
    return jsonify(employees), 200

# GET employee by ID
@app.route('/employees/<int:emp_id>', methods=['GET'])
def get_employee(emp_id):
    employee = next((emp for emp in employees if emp["id"] == emp_id), None)
    if employee:
        return jsonify(employee), 200
    return jsonify({"error": "Employee not found"}), 404

# POST - Add a new employee
@app.route('/employees', methods=['POST'])
def add_employee():
    data = request.get_json()
    required_fields = ["name", "place", "email", "designation", "description"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing fields. Required: {required_fields}"}), 400

    new_employee = {
        "id": len(employees) + 1,
        "name": data["name"],
        "place": data["place"],
        "email": data["email"],
        "designation": data["designation"],
        "description": data["description"],
        "department": data.get("department", "General"),   # optional
        "phone": data.get("phone", "N/A")                  # optional
    }
    employees.append(new_employee)
    return jsonify(new_employee), 201

# PUT - Update employee details
@app.route('/employees/<int:emp_id>', methods=['PUT'])
def update_employee(emp_id):
    data = request.get_json()
    employee = next((emp for emp in employees if emp["id"] == emp_id), None)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    for key, value in data.items():
        if key in employee:
            employee[key] = value
    return jsonify(employee), 200

# DELETE employee
@app.route('/employees/<int:emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    global employees
    employees = [emp for emp in employees if emp["id"] != emp_id]
    return jsonify({"message": f"Employee {emp_id} deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
