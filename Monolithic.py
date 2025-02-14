import random
from typing import List, Dict

class SQLGenerator:
    def __init__(self, target_lines: int):
        self.target_lines = target_lines
        self.current_lines = 0
        self.sql_content: List[str] = []
        
        # Common business entities
        self.entities = {
            'customer': ['customer_id', 'credit_limit', 'status', 'last_order_date', 'total_orders', 'rating'],
            'order': ['order_id', 'customer_id', 'order_date', 'total_amount', 'status', 'shipping_method'],
            'product': ['product_id', 'name', 'price', 'stock_level', 'category', 'supplier_id'],
            'inventory': ['inventory_id', 'product_id', 'warehouse_id', 'quantity', 'last_updated'],
            'payment': ['payment_id', 'order_id', 'amount', 'payment_date', 'payment_method', 'status']
        }
        
    def add_line(self, line: str = "") -> None:
        self.sql_content.append(line)
        self.current_lines += 1

    def generate_realistic_procedure(self, name: str, params: List[Dict[str, str]]) -> None:
        # Procedure header
        param_str = ", ".join([f"{p['name']} IN {p['type']}" for p in params])
        self.add_line(f"CREATE OR REPLACE PROCEDURE {name} (")
        self.add_line(f"    {param_str}")
        self.add_line(") AS")
        
        # Local variables
        self.add_line("    -- Local variables")
        for var in self._generate_local_variables():
            self.add_line(f"    {var}")
        self.add_line("")
        
        self.add_line("BEGIN")
        
        # Input validation
        self.add_line("    -- Validate input parameters")
        self._generate_input_validation()
        self.add_line("")
        
        # Business logic
        self.add_line("    -- Business logic")
        self._generate_business_logic()
        
        # Exception handling
        self.add_line("EXCEPTION")
        self._generate_exception_handling()
        
        self.add_line("END;")
        self.add_line("/")
        self.add_line("")

    def _generate_local_variables(self) -> List[str]:
        vars = [
            "v_error_code NUMBER;",
            "v_error_message VARCHAR2(4000);",
            "v_current_date DATE := SYSDATE;",
            "v_status VARCHAR2(50);",
            "v_count NUMBER;",
            "v_is_valid BOOLEAN := TRUE;"
        ]
        return vars

    def _generate_input_validation(self) -> None:
        self.add_line("    -- Check for null values")
        self.add_line("    IF some_param IS NULL THEN")
        self.add_line("        RAISE_APPLICATION_ERROR(-20001, 'Parameter cannot be null');")
        self.add_line("    END IF;")
        
        self.add_line("")
        self.add_line("    -- Validate data exists")
        self.add_line("    SELECT COUNT(*) INTO v_count")
        self.add_line("    FROM some_table")
        self.add_line("    WHERE id = some_param;")
        
        self.add_line("")
        self.add_line("    IF v_count = 0 THEN")
        self.add_line("        RAISE_APPLICATION_ERROR(-20002, 'Record not found');")
        self.add_line("    END IF;")

    def _generate_business_logic(self) -> None:
        # Select with joins
        self.add_line("    -- Get current status")
        self.add_line("    SELECT t1.status, t2.category")
        self.add_line("    INTO v_status, v_category")
        self.add_line("    FROM table1 t1")
        self.add_line("    INNER JOIN table2 t2 ON t1.id = t2.id")
        self.add_line("    WHERE t1.id = some_param")
        self.add_line("    AND t1.status = 'ACTIVE';")
        self.add_line("")
        
        # Business rules
        self.add_line("    -- Apply business rules")
        self.add_line("    IF v_status = 'PENDING' THEN")
        self.add_line("        -- Calculate new values")
        self.add_line("        v_new_amount := v_current_amount * 1.1;")
        self.add_line("        ")
        self.add_line("        -- Update records")
        self.add_line("        UPDATE table1")
        self.add_line("        SET amount = v_new_amount,")
        self.add_line("            last_updated = v_current_date,")
        self.add_line("            updated_by = user")
        self.add_line("        WHERE id = some_param;")
        self.add_line("    END IF;")
        self.add_line("")
        
        # Insert audit log
        self.add_line("    -- Insert audit record")
        self.add_line("    INSERT INTO audit_log (")
        self.add_line("        transaction_id,")
        self.add_line("        transaction_date,")
        self.add_line("        transaction_type,")
        self.add_line("        user_id,")
        self.add_line("        status")
        self.add_line("    ) VALUES (")
        self.add_line("        audit_seq.NEXTVAL,")
        self.add_line("        v_current_date,")
        self.add_line("        'UPDATE',")
        self.add_line("        user,")
        self.add_line("        'SUCCESS'")
        self.add_line("    );")
        
        self.add_line("    COMMIT;")

    def _generate_exception_handling(self) -> None:
        self.add_line("    WHEN NO_DATA_FOUND THEN")
        self.add_line("        ROLLBACK;")
        self.add_line("        v_error_message := 'No data found for ID: ' || some_param;")
        self.add_line("        RAISE_APPLICATION_ERROR(-20101, v_error_message);")
        self.add_line("")
        self.add_line("    WHEN OTHERS THEN")
        self.add_line("        ROLLBACK;")
        self.add_line("        v_error_code := SQLCODE;")
        self.add_line("        v_error_message := SQLERRM;")
        self.add_line("        ")
        self.add_line("        -- Log error")
        self.add_line("        INSERT INTO error_log (")
        self.add_line("            error_code,")
        self.add_line("            error_message,")
        self.add_line("            created_date")
        self.add_line("        ) VALUES (")
        self.add_line("            v_error_code,")
        self.add_line("            v_error_message,")
        self.add_line("            v_current_date")
        self.add_line("        );")
        self.add_line("        COMMIT;")
        self.add_line("")
        self.add_line("        RAISE;")

    def generate_business_procedures(self) -> None:
        # Customer management procedures
        self.generate_realistic_procedure("update_customer_credit_limit", [
            {"name": "p_customer_id", "type": "NUMBER"},
            {"name": "p_new_credit_limit", "type": "NUMBER"}
        ])
        
        self.generate_realistic_procedure("process_customer_order", [
            {"name": "p_customer_id", "type": "NUMBER"},
            {"name": "p_order_id", "type": "NUMBER"},
            {"name": "p_payment_method", "type": "VARCHAR2"}
        ])
        
        # Order processing procedures
        self.generate_realistic_procedure("validate_order_status", [
            {"name": "p_order_id", "type": "NUMBER"},
            {"name": "p_status", "type": "VARCHAR2"}
        ])
        
        # More procedures can be added here...

    def generate_package(self) -> str:
        """Generate complete package with all procedures"""
        packages = ['CUSTOMER_MGMT', 'ORDER_MGMT', 'INVENTORY_MGMT', 'PAYMENT_MGMT', 'REPORTING_MGMT']
        remaining_lines = self.target_lines
        
        while remaining_lines > 0 and packages:
            package_name = packages.pop(0)
            
            # Package Specification
            self.add_line(f"CREATE OR REPLACE PACKAGE {package_name} AS")
            self.add_line("    /*")
            self.add_line(f"    * Package: {package_name}")
            self.add_line("    * Purpose: Business logic for managing operations")
            self.add_line("    */")
            self.add_line("")
            
            # Generate procedure specifications
            procedure_count = min(remaining_lines // 100, 10)  # Estimate procedures needed
            for i in range(procedure_count):
                if package_name == 'CUSTOMER_MGMT':
                    procs = [
                        ("update_customer_credit_limit", [
                            {"name": "p_customer_id", "type": "NUMBER"},
                            {"name": "p_new_credit_limit", "type": "NUMBER"}
                        ]),
                        ("process_customer_status_change", [
                            {"name": "p_customer_id", "type": "NUMBER"},
                            {"name": "p_new_status", "type": "VARCHAR2"},
                            {"name": "p_reason_code", "type": "VARCHAR2"}
                        ]),
                        ("validate_customer_account", [
                            {"name": "p_customer_id", "type": "NUMBER"},
                            {"name": "p_validation_type", "type": "VARCHAR2"}
                        ])
                    ]
                elif package_name == 'ORDER_MGMT':
                    procs = [
                        ("create_new_order", [
                            {"name": "p_customer_id", "type": "NUMBER"},
                            {"name": "p_order_type", "type": "VARCHAR2"},
                            {"name": "p_total_amount", "type": "NUMBER"}
                        ]),
                        ("update_order_status", [
                            {"name": "p_order_id", "type": "NUMBER"},
                            {"name": "p_new_status", "type": "VARCHAR2"},
                            {"name": "p_update_reason", "type": "VARCHAR2"}
                        ])
                    ]
                else:
                    procs = [
                        ("process_inventory_adjustment", [
                            {"name": "p_product_id", "type": "NUMBER"},
                            {"name": "p_quantity_change", "type": "NUMBER"},
                            {"name": "p_reason_code", "type": "VARCHAR2"}
                        ]),
                        ("generate_inventory_report", [
                            {"name": "p_warehouse_id", "type": "NUMBER"},
                            {"name": "p_report_type", "type": "VARCHAR2"}
                        ])
                    ]
                
                # Generate procedure specification
                for proc_name, params in procs:
                    param_str = ", ".join([f"{p['name']} IN {p['type']}" for p in params])
                    self.add_line(f"    PROCEDURE {proc_name}({param_str});")
                    self.add_line("")
            
            self.add_line(f"END {package_name};")
            self.add_line("/")
            self.add_line("")
            
            # Package Body
            self.add_line(f"CREATE OR REPLACE PACKAGE BODY {package_name} AS")
            
            # Generate procedure implementations
            for proc_name, params in procs:
                self.generate_realistic_procedure(proc_name, params)
            
            self.add_line(f"END {package_name};")
            self.add_line("/")
            self.add_line("")
            
            remaining_lines = self.target_lines - self.current_lines
            
        return "\n".join(self.sql_content)

def generate_sql_file(target_lines: int, output_file: str = "code.sql") -> None:
    generator = SQLGenerator(target_lines)
    sql_content = generator.generate_package()
    
    with open(output_file, 'w') as f:
        f.write(sql_content)
    
    print(f"Generated {generator.current_lines} lines of SQL code in {output_file}")

if __name__ == "__main__":
    target_lines = int(input("Enter desired number of lines of SQL code: "))
    generate_sql_file(target_lines)