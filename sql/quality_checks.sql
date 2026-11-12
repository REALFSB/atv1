-- =============================================================================
-- DataTrack · Consultas de validação de qualidade (Aula 9 · US11)
-- Dialeto: SQLite 3 (portável para PostgreSQL trocando julianday() por datas)
--
-- Tabela esperada: employees (base normalizada por src/validate.py::normalize)
--   * textos vazios  -> NULL
--   * Hire_Date      -> 'AAAA-MM-DD'
--   * Resigned       -> 'True' | 'False'
--
-- Cada consulta QCxx devolve UMA linha: avaliados, aprovados, reprovados.
-- src/validate.py executa estas consultas e os testes exigem que o resultado
-- seja idêntico ao motor pandas (paridade SQL = pandas).
-- Data de referência: 2024-09-04 (data de extração da base Kaggle).
-- =============================================================================

-- name: QC01
-- Completude: campos obrigatórios preenchidos (meta 100%, crítica)
SELECT
    COUNT(*)                                                    AS avaliados,
    SUM(CASE WHEN Employee_ID IS NOT NULL AND Department IS NOT NULL
              AND Gender IS NOT NULL AND Age IS NOT NULL
              AND Hire_Date IS NOT NULL AND Years_At_Company IS NOT NULL
              AND Monthly_Salary IS NOT NULL AND Resigned IS NOT NULL
             THEN 1 ELSE 0 END)                                 AS aprovados,
    SUM(CASE WHEN Employee_ID IS NULL OR Department IS NULL
              OR Gender IS NULL OR Age IS NULL
              OR Hire_Date IS NULL OR Years_At_Company IS NULL
              OR Monthly_Salary IS NULL OR Resigned IS NULL
             THEN 1 ELSE 0 END)                                 AS reprovados
FROM employees;

-- name: QC02
-- Unicidade: Employee_ID não se repete (todas as ocorrências do ID repetido reprovam)
WITH contagem AS (
    SELECT Employee_ID, COUNT(*) AS n
    FROM employees
    WHERE Employee_ID IS NOT NULL
    GROUP BY Employee_ID
)
SELECT
    SUM(n)                                   AS avaliados,
    SUM(CASE WHEN n = 1 THEN n ELSE 0 END)   AS aprovados,
    SUM(CASE WHEN n > 1 THEN n ELSE 0 END)   AS reprovados
FROM contagem;

-- name: QC03
-- Validade de domínio: categorias dentro do catálogo (NULL é tratado em QC01)
WITH marcado AS (
    SELECT CASE WHEN
           (Department IS NOT NULL AND Department NOT IN
               ('Customer Support','Engineering','Finance','HR','IT',
                'Legal','Marketing','Operations','Sales'))
        OR (Gender IS NOT NULL AND Gender NOT IN ('Female','Male','Other'))
        OR (Education_Level IS NOT NULL AND Education_Level NOT IN
               ('High School','Bachelor','Master','PhD'))
        OR (Job_Title IS NOT NULL AND Job_Title NOT IN
               ('Analyst','Consultant','Developer','Engineer','Manager',
                'Specialist','Technician'))
        OR (Resigned IS NOT NULL AND Resigned NOT IN ('True','False'))
    THEN 1 ELSE 0 END AS falha
    FROM employees
)
SELECT COUNT(*) AS avaliados, COUNT(*) - SUM(falha) AS aprovados, SUM(falha) AS reprovados
FROM marcado;

-- name: QC04
-- Validade de faixa: valores numéricos dentro dos limites de negócio
WITH marcado AS (
    SELECT CASE WHEN
           (Age IS NOT NULL AND (Age < 18 OR Age > 70))
        OR (Years_At_Company IS NOT NULL AND (Years_At_Company < 0 OR Years_At_Company > 60))
        OR (Performance_Score IS NOT NULL AND (Performance_Score < 1 OR Performance_Score > 5))
        OR (Employee_Satisfaction_Score IS NOT NULL
            AND (Employee_Satisfaction_Score < 1.0 OR Employee_Satisfaction_Score > 5.0))
        OR (Monthly_Salary IS NOT NULL AND (Monthly_Salary < 1 OR Monthly_Salary > 100000))
        OR (Work_Hours_Per_Week IS NOT NULL
            AND (Work_Hours_Per_Week < 1 OR Work_Hours_Per_Week > 80))
        OR (Sick_Days IS NOT NULL AND (Sick_Days < 0 OR Sick_Days > 365))
    THEN 1 ELSE 0 END AS falha
    FROM employees
)
SELECT COUNT(*) AS avaliados, COUNT(*) - SUM(falha) AS aprovados, SUM(falha) AS reprovados
FROM marcado;

-- name: QC05
-- Consistência: Years_At_Company = (2024-09-04 - Hire_Date) em dias // 365
-- e Hire_Date não pode ser posterior à data de referência
WITH base AS (
    SELECT
        Years_At_Company,
        CAST(julianday('2024-09-04') - julianday(Hire_Date) AS INTEGER) AS dias
    FROM employees
    WHERE Hire_Date IS NOT NULL AND Years_At_Company IS NOT NULL
)
SELECT
    COUNT(*)                                                             AS avaliados,
    SUM(CASE WHEN dias >= 0 AND dias / 365 = Years_At_Company THEN 1 ELSE 0 END) AS aprovados,
    SUM(CASE WHEN dias < 0 OR dias / 365 <> Years_At_Company THEN 1 ELSE 0 END)  AS reprovados
FROM base;

-- name: QC06
-- Consistência: idade na admissão (Age - Years_At_Company) >= 18
SELECT
    COUNT(*)                                                           AS avaliados,
    SUM(CASE WHEN Age - Years_At_Company >= 18 THEN 1 ELSE 0 END)      AS aprovados,
    SUM(CASE WHEN Age - Years_At_Company <  18 THEN 1 ELSE 0 END)      AS reprovados
FROM employees
WHERE Age IS NOT NULL AND Years_At_Company IS NOT NULL;

-- name: QC06_falhas
-- Investigação (não faz parte da paridade): registros que violam QC06,
-- com a idade implícita na admissão. Usado no relatório SBAR.
SELECT Employee_ID, Department, Job_Title, Age, Years_At_Company,
       Age - Years_At_Company AS idade_na_admissao
FROM employees
WHERE Age IS NOT NULL AND Years_At_Company IS NOT NULL
  AND Age - Years_At_Company < 18
ORDER BY idade_na_admissao, Employee_ID;
