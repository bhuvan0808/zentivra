## Runs Lifecycle

### Scenario: No runs so far



1. Run is the heart of the application
2. They'll trigger agents parallelly to perform their respective tasks
3. To create a run, we have a 3-step process which starts when the user clicks on Configure Run button, this will redirect the user to a next pagee and 3 steps start from here
4. Step-1: User provides Run Name\*, Description, enable PDF gen, enable email alert (both are bools, based on toggle value, we'll work, at least one should be turned on)
5. Step-2: User selects the sources he wants to use for this run, by default all will be selected, there'd be a checkbox at the start of each record and a checkbox to select/unselect all records. The user can search the available sources and filter them based on the sources' agent type
6. Step-3: The user will give config values like Trigger Frequencyy, Crawl Depth and keywords. The user can give these either via UI (input fields) or by selecting an option called code, which will replace the form with code editor, 2 langs are supported, JSON and YML. the user can select btw the 2 based on his choice
7. In the same page, the user can create a run or create and trigger the run
8. All these details are stored in the DB. These runs once created can be triggered again later manually. refer to the DB schema for more info. in the runs page, the user can edit the run. crud ops can be performed on each run.
9. One run can have multiple triggers, in runs page, each run record can be expanded, like an accordion to show the triggers history.



## What should happen when a run is triggered

1\. Run Execution Record Creation

A new record is created in the RUN\_EXECUTIONS table.  

This represents one execution instance of the run.  

The execution record stores metadata such as:

\- run\_id

\- trigger\_method (manual / scheduled)

\- status (started, running, completed, failed)

\- started\_at



This record acts as the parent reference for all downstream operations like crawling, findings generation, snapshots, and digests.



2\. Source Resolution

The system fetches the list of sources configured for the run from the RUNS table.  

Each source corresponds to an agent/crawler responsible for gathering information.



Example:

Run → Sources  

\- OpenAI crawler  

\- Anthropic crawler  

\- Research papers crawler  

\- AI news crawler  



3\. Parallel Agent Execution

For the given execution, the system triggers all configured agents in parallel.



Each agent performs:

\- crawling or API calls

\- scraping or extracting relevant content

\- filtering content using the configured keywords

\- respecting the configured crawl depth



Each agent processes its data independently.



4\. Findings Extraction

During crawling, agents extract relevant insights and store them in the FINDINGS table.



Each finding typically contains:

\- content (markdown formatted text)

\- summary

\- category

\- confidence score

\- source URL

\- run\_execution\_id reference



These findings represent the raw intelligence gathered during the execution.



5\. Snapshot Creation

Once an agent finishes processing its assigned source, a snapshot is created.



A snapshot represents the grouped output of a single source during one run execution.



The snapshot includes:

\- run\_execution\_id

\- source\_id

\- total findings count

\- optional summary

\- status



For example, if four sources are configured for the run, four snapshots will be generated for that execution.



Snapshots provide a frozen view of what each source produced at that time.



6\. Snapshot Completion

When all agents complete execution and their snapshots are generated, the execution status is updated.



RUN\_EXECUTIONS.status → completed



At this point the system has:

\- multiple findings

\- multiple snapshots

\- one run execution



7\. Digest Generation

If the run configuration has PDF generation enabled, the system begins digest creation.



The digest generation process:

\- collects all snapshots belonging to the run execution

\- aggregates their findings

\- uses an LLM to summarize and structure the insights

\- generates a consolidated report



The report includes sections such as:

\- key updates

\- major announcements

\- research highlights

\- trends or patterns



8\. Digest Storage

The generated digest is stored in the DIGESTS table.



Stored fields include:

\- run\_execution\_id

\- pdf\_path

\- html\_path

\- created\_at



The relationship between snapshots and digests is maintained using the DIGEST\_SNAPSHOTS table.



This allows a digest to reference multiple snapshots used to generate the report.



9\. Email Notification (Optional)

If email alerts are enabled in the run configuration, the system sends the generated digest to configured recipients.



The email typically contains:

\- summary of findings

\- link to the HTML digest

\- PDF attachment (optional)



10\. Run Completion

Once digest generation and notifications are complete, the execution lifecycle ends.



The run execution remains stored in the RUN\_EXECUTIONS table and can be viewed from the Runs page.



Users can expand a run in the UI to see:

\- trigger history

\- execution status

\- generated digests

\- associated findings

