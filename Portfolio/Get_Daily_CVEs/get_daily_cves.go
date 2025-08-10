/* Export GET_DAILY_CVES_DB environment variable before running:

export GET_DAILY_CVES_DB=<DB username,password and URL*/

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

/* The CveInfo struct is where the response from the NIST CVE API
is unmarshalled to. Only certain fields that we want are in the
struct */

type Cve struct {
	Cve []CveInfo `json:"vulnerabilities"`
}

type CveInfo struct {
	Cve struct {
		ID               string `json:"id"`
		SourceIdentifier string `json:"sourceIdentifier"`
		Published        string `json:"published"`
		LastModified     string `json:"lastModified"`
		Descriptions     []struct {
			Lang  string `json:"lang"`
			Value string `json:"value"`
		} `json:"descriptions"`
		Metrics struct {
			CvssMetricV40 []struct {
				CvssData struct {
					BaseScore float64 `json:"baseScore"`
				} `json:"cvssData"`
			} `json:"cvssMetricV40"`
			CvssMetricV31 []struct {
				CvssData struct {
					BaseScore float64 `json:"baseScore"`
				} `json:"cvssData"`
			} `json:"cvssMetricV31"`
			CvssMetricV30 []struct {
				CvssData struct {
					BaseScore float64 `json:"baseScore"`
				} `json:"cvssData"`
			} `json:"cvssMetricV30"`
			CvssMetricV2 []struct {
				CvssData struct {
					BaseScore float64 `json:"baseScore"`
				} `json:"cvssData"`
			} `"json:"cvssMetricV2"`
		} `json:"metrics"`
		References []struct {
			URL    string `json:"url"`
			Source string `json:"source"`
		} `json:"references"`
	} `json:"cve"`
}

func main() {
	poolConfig, err := pgxpool.ParseConfig(os.Getenv("GET_DAILY_CVES_DB"))
	if err != nil {
		log.Fatal("Error parsing pgx config: ", err)
	}

	poolConfig.BeforeAcquire = func(ctx context.Context, conn *pgx.Conn) bool {
		RegisterDataTypes(ctx, conn)
		return true
	}
	dbPool, err := pgxpool.NewWithConfig(context.Background(), poolConfig)
	if err != nil {
		log.Fatal("Error connecting to database: ", err)
	}

	defer dbPool.Close()

	url := createOrUseCVETable(dbPool)
	insertCVEs(dbPool, url)
}

func RegisterDataTypes(ctx context.Context, conn *pgx.Conn) error {
	dataTypeNames := []string{
		"CveInfo",
		"_CveInfo",
		"Cve",
		"_Cve",
	}

	for _, typeName := range dataTypeNames {
		dataType, err := conn.LoadType(ctx, typeName)
		if err != nil {
			return err
		}
		conn.TypeMap().RegisterType(dataType)
	}

	return nil
}

// Create the dailycves table or use the existing one
func createOrUseCVETable(dbPool *pgxpool.Pool) (cveURL string) {
	url := cveURL
	var tableExists bool
	var tableNotEmpty bool
	var postgreDateAsString string
	createTableQuery := `CREATE TABLE IF NOT EXISTS dailycves (
		     id TEXT,
		     source TEXT,
		     published TIMESTAMPTZ,
		     lastmodified TIMESTAMPTZ,
			 basescore FLOAT,
			 description TEXT
	    )`
	// TODO: Maybe add "id SERIAL PRIMARY KEY", "cve_references TEXT"

	// Check if dailycves table is in the database
	if err := dbPool.QueryRow(context.Background(), "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'dailycves')").Scan(&tableExists); err != nil {
		log.Fatal("Error when trying to determine if dailycves table in database ", err)
	}

	// If dailycves table is not in the database
	if tableExists == false {
		fmt.Println("dailycves table is not in database; creating table")
		_, err := dbPool.Exec(context.Background(), createTableQuery)
		if err != nil {
			log.Fatal("Error creating dailycves table ", err)
		}

		//Need? defer dbPool.Close()

		currentDate := time.Now().Format("2006-01-02")
		url = "https://services.nvd.nist.gov/rest/json/cves/2.0/?pubStartDate=" + currentDate + "T00:00:00.000&pubEndDate=" + currentDate + "T23:59:59.999"

		return url

		// If dailycves table is in the database
	} else if tableExists == true {
		// Check if dailycves table is empty
		if err := dbPool.QueryRow(context.Background(), "SELECT EXISTS (SELECT * FROM dailycves)").Scan(&tableNotEmpty); err != nil {
			log.Fatal("Error when trying to determine if dailycves table is empty", err)
		}

		// If dailycves table is empty
		if tableNotEmpty == false {
			fmt.Println("dailycves table is empty")
			currentDate := time.Now().Format("2006-01-02")
			url = "https://services.nvd.nist.gov/rest/json/cves/2.0/?pubStartDate=" + currentDate + "T00:00:00.000&pubEndDate=" + currentDate + "T23:59:59.999"

			return url

			// If dailycves table is not empty
		} else if tableNotEmpty == true {

			currentDate, err := time.Parse("2006-01-02 15:04:05", (time.Now().Format("2006-01-02 15:04:05")))
			if err != nil {
				log.Fatal("Error parsing current time: ", err)
			}

			/* Get of last record in dailycves table so that date can be checked to see if table
			contains additional CVEs for today. Not getting in MM-YYYY format as we want to
			check the date and time. Query will store date as a string in YYYY-MM HH:MM:SS
			format.*/

			if err := dbPool.QueryRow(context.Background(), "SELECT SUBSTRING(CAST(published AS TEXT), 1, 19) FROM dailycves ORDER BY published DESC LIMIT 1").Scan(&postgreDateAsString); err != nil {
				log.Fatal("Error when trying to determine if dailycves table contains yesterday's CVEs (Error when trying to get of last record in dailycves table): ", err)
			}

			tempString := strings.Split(postgreDateAsString, " ")
			postgreDateAsStringDateOnly := tempString[0]

			currentDateAsStringDateOnly := currentDate.Format("2006-01-02")

			postgreDate, err := time.Parse("2006-01-02 15:04:05", postgreDateAsString)
			if err != nil {
				log.Fatal("Error when trying to convert date of last record in dailycves table to time.Time format: ", err)
			}

			// If the current date/time are later that the date/time in the database and it is still the current day
			if currentDate.After(postgreDate) && currentDateAsStringDateOnly == postgreDateAsStringDateOnly {

				postgreDateAsString := strings.TrimRight(postgreDate.Format(time.RFC3339), "Z")

				url = "https://services.nvd.nist.gov/rest/json/cves/2.0/?pubStartDate=" + postgreDateAsString + ".000&pubEndDate=" + currentDateAsStringDateOnly + "T23:59:59.999"

				//Need? defer dbPool.Close()

				return url
			} else {

				currentDate, err := time.Parse("2006-01-02", (time.Now().Format("2006-01-02")))
				if err != nil {
					log.Fatal("Error parsing current time: ", err)
				}

				/* Get YYYY-MM of last record in dailycves table so that date can be checked to see
				if table contains yesterday's CVEs. If so, drop the table and add the current day's
				CVEs */
				if err := dbPool.QueryRow(context.Background(), "SELECT SUBSTRING(CAST(published AS TEXT), 1, 10) FROM dailycves ORDER BY published DESC LIMIT 1").Scan(&postgreDateAsString); err != nil {
					log.Fatal("Error when trying to determine if dailycves table contains yesterday's CVEs (Error when trying to get of last record in dailycves table): ", err)
				}
				postgreDate, err := time.Parse("2006-01-02", postgreDateAsString)
				if err != nil {
					log.Fatal("Error when trying to convert date of last record in dailycves table to time.Time format: ", err)
				}

				fmt.Println("Date of last record in DB as a time.Time value", postgreDate)

				if currentDate.After(postgreDate) {
					fmt.Println("Previous day's CVEs in dailycves table. Dropping table")

					if _, err := dbPool.Exec(context.Background(), "DROP TABLE dailycves"); err != nil {
						log.Fatal("Could not drop dailycves table containing yesterday's CVEs: ", err)
					}

					fmt.Println("dailycves table is not in database; creating table")
					_, err := dbPool.Exec(context.Background(), createTableQuery)
					if err != nil {
						log.Fatal("Error creating dailycves table: ", err)
					}

					currentDate := time.Now().Format("2006-01-02")
					url = "https://services.nvd.nist.gov/rest/json/cves/2.0/?pubStartDate=" + currentDate + "T00:00:00.000&pubEndDate=" + currentDate + "T23:59:59.999"

					//Need? defer dbPool.Close()

					return url

				}
			}
		}
	}
	return url
}

// Get the CVEs from the NIST CVE API
func getDailyCVEs(url string) (Cve, error) {
	cves := Cve{}
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return cves, err
	}

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		return cves, err
	}

	resBody, err := io.ReadAll(res.Body)
	if err != nil {
		return cves, err
	}

	err = json.Unmarshal(resBody, &cves)
	if err != nil {
		return cves, err
	}

	return cves, nil
}

// Insert the CVEs into the dailycves table
func insertCVEs(dbPool *pgxpool.Pool, url string) {
	cves, err := getDailyCVEs(url)
	fmt.Println("Getting daily CVEs from NIST CVE API")
	if err != nil {
		log.Fatal("Could not get CVEs from NIST CVE API: ", err)
	}

	entries := [][]any{}
	columns := []string{"id", "source", "published", "lastmodified", "basescore", "description"}
	tableName := "dailycves"

	layout := "2006-01-02T15:04:05.000"

	for _, dailycves := range cves.Cve {

		/* The API provides the Published and Last Modified times as strings so they
		   are converted to TIMESTAMPTZ for Postgre for use by clients if they need to
		   query by timestamp */
		publishedInTIMESTAMPTZ, err := time.Parse(layout, dailycves.Cve.Published)
		if err != nil {
			log.Fatal("Could not convert Published time to TIMESTAMPTZ ", err)
		}

		lastModifiedInTIMESTAMPTZ, err := time.Parse(layout, dailycves.Cve.LastModified)
		if err != nil {
			log.Fatal("Could not convert Last Modified time to TIMESTAMPTZ ", err)
		}

		// Check each of the possible basescore types
		var baseScore float64 = 0.0

		if dailycves.Cve.Metrics.CvssMetricV40 != nil {
			baseScore = dailycves.Cve.Metrics.CvssMetricV40[0].CvssData.BaseScore

		} else if dailycves.Cve.Metrics.CvssMetricV31 != nil {
			baseScore = dailycves.Cve.Metrics.CvssMetricV31[0].CvssData.BaseScore

		} else if dailycves.Cve.Metrics.CvssMetricV30 != nil {
			baseScore = dailycves.Cve.Metrics.CvssMetricV30[0].CvssData.BaseScore

		} else if dailycves.Cve.Metrics.CvssMetricV2 != nil {
			baseScore = dailycves.Cve.Metrics.CvssMetricV2[0].CvssData.BaseScore

		} else { // basescore was not found so set to 0.0
			baseScore = 0.0
		}

		/* dailycves.Cve.Descriptions[0].Value is in bytes so use string() to convert. Otherwise
		   "panic: runtime error: index out of range [0] with length 0" occurs Could also use
		   "description JSONB" when creating the table*/
		entries = append(entries, []any{dailycves.Cve.ID, dailycves.Cve.SourceIdentifier, publishedInTIMESTAMPTZ, lastModifiedInTIMESTAMPTZ, baseScore, string(dailycves.Cve.Descriptions[0].Value)})
	}

	// Bulk insert the CVEs into the dailycves table
	_, err = dbPool.CopyFrom(
		context.Background(),
		pgx.Identifier{tableName},
		columns,
		pgx.CopyFromRows(entries),
	)

	if err != nil {
		fmt.Printf("Error copying into %s table: %s", tableName, err)
	} else {
		fmt.Println("CVEs have been copied to dailycves table")
	}
}
