CREATE OR REPLACE PACKAGE CUSTOMER_MGMT AS
    /*
    * Package: CUSTOMER_MGMT
    * Purpose: Business logic for managing operations
    */

    PROCEDURE update_customer_credit_limit(p_customer_id IN NUMBER, p_new_credit_limit IN NUMBER);

   
END CUSTOMER_MGMT;
/

CREATE OR REPLACE PACKAGE BODY CUSTOMER_MGMT AS
CREATE OR REPLACE PROCEDURE update_customer_credit_limit (
    p_customer_id IN NUMBER, p_new_credit_limit IN NUMBER
) AS
    -- Local variables
    v_error_code NUMBER;
    v_error_message VARCHAR2(4000);
    v_current_date DATE := SYSDATE;
    v_status VARCHAR2(50);
    v_count NUMBER;
    v_is_valid BOOLEAN := TRUE;

BEGIN
    -- Validate input parameters
    -- Check for null values
    IF some_param IS NULL THEN
        RAISE_APPLICATION_ERROR(-20001, 'Parameter cannot be null');
    END IF;

    -- Validate data exists
    SELECT COUNT(*) INTO v_count
    FROM some_table
    WHERE id = some_param;

    IF v_count = 0 THEN
        RAISE_APPLICATION_ERROR(-20002, 'Record not found');
    END IF;

    -- Business logic
    -- Get current status
    SELECT t1.status, t2.category
    INTO v_status, v_category
    FROM table1 t1
    INNER JOIN table2 t2 ON t1.id = t2.id
    WHERE t1.id = some_param
    AND t1.status = 'ACTIVE';

    -- Apply business rules
    IF v_status = 'PENDING' THEN
        -- Calculate new values
        v_new_amount := v_current_amount * 1.1;
        
        -- Update records
        UPDATE table1
        SET amount = v_new_amount,
            last_updated = v_current_date,
            updated_by = user
        WHERE id = some_param;
    END IF;

    -- Insert audit record
    INSERT INTO audit_log (
        transaction_id,
        transaction_date,
        transaction_type,
        user_id,
        status
    ) VALUES (
        audit_seq.NEXTVAL,
        v_current_date,
        'UPDATE',
        user,
        'SUCCESS'
    );
    COMMIT;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        ROLLBACK;
        v_error_message := 'No data found for ID: ' || some_param;
        RAISE_APPLICATION_ERROR(-20101, v_error_message);

    WHEN OTHERS THEN
        ROLLBACK;
        v_error_code := SQLCODE;
        v_error_message := SQLERRM;
        
        -- Log error
        INSERT INTO error_log (
            error_code,
            error_message,
            created_date
        ) VALUES (
            v_error_code,
            v_error_message,
            v_current_date
        );
        COMMIT;

        RAISE;
END;
/
END CUSTOMER_MGMT;
/