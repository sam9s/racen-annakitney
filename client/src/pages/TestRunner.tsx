import { useState, useCallback, useEffect } from "react";
import { useLocation } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { CheckCircle, XCircle, PlayCircle, Loader2, AlertCircle } from "lucide-react";

interface TestAssertion {
  must_contain?: string[];
  must_not_contain?: string[];
  min_events?: number;
  url_pattern?: string;
}

interface TestTurn {
  query: string;
  expected_intent?: string;
  assertions?: TestAssertion;
}

interface TestScenario {
  id: string;
  category: string;
  name: string;
  query?: string;
  expected_intent?: string;
  assertions?: TestAssertion;
  multi_turn?: boolean;
  turns?: TestTurn[];
}

interface TestResult {
  id: string;
  name: string;
  category: string;
  status: "pass" | "fail" | "running" | "pending";
  duration?: number;
  details: {
    query: string;
    response: string;
    intent: string;
    expected_intent: string;
    assertions_passed: string[];
    assertions_failed: string[];
  }[];
}

export default function TestRunner() {
  const [, setLocation] = useLocation();
  const [scenarios, setScenarios] = useState<TestScenario[]>([]);
  const [results, setResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [selectedResult, setSelectedResult] = useState<TestResult | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>("all");

  useEffect(() => {
    const accessGranted = sessionStorage.getItem("testRunnerAccess");
    if (!accessGranted) {
      setLocation("/");
    }
  }, [setLocation]);

  const loadScenarios = useCallback(async (): Promise<TestScenario[]> => {
    try {
      const response = await fetch("/tests/comprehensive_test_scenarios.json");
      const data = await response.json();
      const loadedScenarios = data.test_scenarios as TestScenario[];
      setScenarios(loadedScenarios);
      setResults(loadedScenarios.map((s: TestScenario) => ({
        id: s.id,
        name: s.name,
        category: s.category,
        status: "pending" as const,
        details: []
      })));
      return loadedScenarios;
    } catch (error) {
      console.error("Failed to load scenarios:", error);
      return [];
    }
  }, []);

  const checkAssertions = (response: string, assertions?: TestAssertion): { passed: string[], failed: string[] } => {
    const passed: string[] = [];
    const failed: string[] = [];

    if (!assertions) return { passed, failed };

    if (assertions.must_contain) {
      for (const term of assertions.must_contain) {
        if (response.toLowerCase().includes(term.toLowerCase())) {
          passed.push(`Contains "${term}"`);
        } else {
          failed.push(`Missing "${term}"`);
        }
      }
    }

    if (assertions.must_not_contain) {
      for (const term of assertions.must_not_contain) {
        if (!response.toLowerCase().includes(term.toLowerCase())) {
          passed.push(`Correctly excludes "${term}"`);
        } else {
          failed.push(`Should not contain "${term}"`);
        }
      }
    }

    if (assertions.url_pattern) {
      if (response.includes(assertions.url_pattern)) {
        passed.push(`URL pattern "${assertions.url_pattern}" found`);
      } else {
        failed.push(`URL pattern "${assertions.url_pattern}" missing`);
      }
    }

    if (assertions.min_events) {
      const eventCount = (response.match(/^\d+\./gm) || []).length;
      if (eventCount >= assertions.min_events) {
        passed.push(`Has ${eventCount} events (min: ${assertions.min_events})`);
      } else {
        failed.push(`Only ${eventCount} events (expected min: ${assertions.min_events})`);
      }
    }

    return { passed, failed };
  };

  const runTest = async (scenario: TestScenario): Promise<TestResult> => {
    const sessionId = `test_${scenario.id}_${Date.now()}`;
    const startTime = Date.now();
    const details: TestResult["details"] = [];

    try {
      if (scenario.multi_turn && scenario.turns) {
        for (const turn of scenario.turns) {
          const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: turn.query, session_id: sessionId })
          });
          const data = await response.json();
          const { passed, failed } = checkAssertions(data.response, turn.assertions);
          
          details.push({
            query: turn.query,
            response: data.response,
            intent: data.intent || "unknown",
            expected_intent: turn.expected_intent || "",
            assertions_passed: passed,
            assertions_failed: failed
          });
        }
      } else {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: scenario.query, session_id: sessionId })
        });
        const data = await response.json();
        const { passed, failed } = checkAssertions(data.response, scenario.assertions);
        
        details.push({
          query: scenario.query || "",
          response: data.response,
          intent: data.intent || "unknown",
          expected_intent: scenario.expected_intent || "",
          assertions_passed: passed,
          assertions_failed: failed
        });
      }

      const allFailed = details.flatMap(d => d.assertions_failed);
      const intentMismatches = details.filter(d => 
        d.expected_intent && d.intent !== d.expected_intent
      );

      return {
        id: scenario.id,
        name: scenario.name,
        category: scenario.category,
        status: allFailed.length === 0 && intentMismatches.length === 0 ? "pass" : "fail",
        duration: Date.now() - startTime,
        details
      };
    } catch (error) {
      return {
        id: scenario.id,
        name: scenario.name,
        category: scenario.category,
        status: "fail",
        duration: Date.now() - startTime,
        details: [{
          query: scenario.query || scenario.turns?.[0]?.query || "",
          response: `Error: ${error}`,
          intent: "error",
          expected_intent: scenario.expected_intent || "",
          assertions_passed: [],
          assertions_failed: [`Test error: ${error}`]
        }]
      };
    }
  };

  const runAllTests = async () => {
    let testScenarios = scenarios;
    if (testScenarios.length === 0) {
      testScenarios = await loadScenarios();
    }
    
    if (testScenarios.length === 0) {
      console.error("No test scenarios loaded");
      return;
    }
    
    setIsRunning(true);
    setProgress(0);
    
    for (let i = 0; i < testScenarios.length; i++) {
      const scenario = testScenarios[i];
      
      setResults(prev => prev.map(r => 
        r.id === scenario.id ? { ...r, status: "running" as const } : r
      ));
      
      const result = await runTest(scenario);
      
      setResults(prev => prev.map(r => 
        r.id === scenario.id ? result : r
      ));
      
      setProgress(((i + 1) / testScenarios.length) * 100);
    }
    
    setIsRunning(false);
  };

  const runFilteredTests = async () => {
    let testScenarios = scenarios;
    if (testScenarios.length === 0) {
      testScenarios = await loadScenarios();
    }
    
    if (testScenarios.length === 0) {
      console.error("No test scenarios loaded");
      return;
    }
    
    const filtered = filterCategory === "all" 
      ? testScenarios 
      : testScenarios.filter(s => s.category === filterCategory);
    
    setIsRunning(true);
    setProgress(0);
    
    for (let i = 0; i < filtered.length; i++) {
      const scenario = filtered[i];
      
      setResults(prev => prev.map(r => 
        r.id === scenario.id ? { ...r, status: "running" as const } : r
      ));
      
      const result = await runTest(scenario);
      
      setResults(prev => prev.map(r => 
        r.id === scenario.id ? result : r
      ));
      
      setProgress(((i + 1) / filtered.length) * 100);
    }
    
    setIsRunning(false);
  };

  const passCount = results.filter(r => r.status === "pass").length;
  const failCount = results.filter(r => r.status === "fail").length;
  const categories = [...new Set(scenarios.map(s => s.category))];

  const filteredResults = filterCategory === "all" 
    ? results 
    : results.filter(r => r.category === filterCategory);

  return (
    <div className="flex h-screen bg-background" data-testid="page-test-runner">
      <div className="flex-1 flex flex-col p-6 gap-4 overflow-hidden">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-semibold" data-testid="text-title">Chatbot Test Runner</h1>
            <p className="text-muted-foreground">End-to-end tests through the actual chat interface</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <select 
              className="border rounded-md px-3 py-2 text-sm"
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              data-testid="select-category"
            >
              <option value="all">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
            <Button 
              onClick={loadScenarios} 
              variant="outline"
              disabled={isRunning}
              data-testid="button-load"
            >
              Load Tests
            </Button>
            <Button 
              onClick={filterCategory === "all" ? runAllTests : runFilteredTests}
              disabled={isRunning || scenarios.length === 0}
              data-testid="button-run"
            >
              {isRunning ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <PlayCircle className="mr-2 h-4 w-4" />
                  Run {filterCategory === "all" ? "All" : filterCategory} Tests
                </>
              )}
            </Button>
          </div>
        </div>

        {isRunning && (
          <div className="space-y-2">
            <Progress value={progress} className="h-2" />
            <p className="text-sm text-muted-foreground">{Math.round(progress)}% complete</p>
          </div>
        )}

        <div className="flex items-center gap-4">
          <Badge variant="outline" className="gap-1">
            <CheckCircle className="h-3 w-3 text-green-500" />
            {passCount} Passed
          </Badge>
          <Badge variant="outline" className="gap-1">
            <XCircle className="h-3 w-3 text-red-500" />
            {failCount} Failed
          </Badge>
          <Badge variant="outline" className="gap-1">
            <AlertCircle className="h-3 w-3 text-muted-foreground" />
            {results.filter(r => r.status === "pending").length} Pending
          </Badge>
        </div>

        <div className="flex-1 flex gap-4 overflow-hidden">
          <Card className="flex-1 overflow-hidden">
            <CardHeader className="py-3">
              <CardTitle className="text-base">Test Results</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[calc(100vh-280px)]">
                <div className="p-4 space-y-2">
                  {filteredResults.map(result => (
                    <div
                      key={result.id}
                      className={`p-3 rounded-md border cursor-pointer transition-colors ${
                        selectedResult?.id === result.id ? "bg-accent" : "hover-elevate"
                      }`}
                      onClick={() => setSelectedResult(result)}
                      data-testid={`test-result-${result.id}`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2 min-w-0">
                          {result.status === "pass" && <CheckCircle className="h-4 w-4 text-green-500 shrink-0" />}
                          {result.status === "fail" && <XCircle className="h-4 w-4 text-red-500 shrink-0" />}
                          {result.status === "running" && <Loader2 className="h-4 w-4 animate-spin shrink-0" />}
                          {result.status === "pending" && <AlertCircle className="h-4 w-4 text-muted-foreground shrink-0" />}
                          <span className="text-sm font-medium truncate">{result.name}</span>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <Badge variant="secondary" className="text-xs">{result.category}</Badge>
                          {result.duration && (
                            <span className="text-xs text-muted-foreground">{result.duration}ms</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          <Card className="flex-1 overflow-hidden">
            <CardHeader className="py-3">
              <CardTitle className="text-base">
                {selectedResult ? selectedResult.name : "Test Details"}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[calc(100vh-280px)]">
                {selectedResult ? (
                  <div className="p-4 space-y-4">
                    {selectedResult.details.map((detail, idx) => (
                      <div key={idx} className="space-y-3">
                        <div className="space-y-1">
                          <p className="text-xs font-medium text-muted-foreground">USER QUERY</p>
                          <p className="text-sm bg-blue-50 dark:bg-blue-950 p-2 rounded-md">{detail.query}</p>
                        </div>
                        
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <p className="text-xs font-medium text-muted-foreground">INTENT</p>
                            <Badge 
                              variant={detail.intent === detail.expected_intent ? "default" : "destructive"}
                              className="text-xs"
                            >
                              {detail.intent}
                            </Badge>
                            {detail.expected_intent && detail.intent !== detail.expected_intent && (
                              <span className="text-xs text-muted-foreground">
                                (expected: {detail.expected_intent})
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="space-y-1">
                          <p className="text-xs font-medium text-muted-foreground">BOT RESPONSE</p>
                          <div className="text-sm bg-muted p-3 rounded-md max-h-48 overflow-y-auto whitespace-pre-wrap">
                            {detail.response}
                          </div>
                        </div>

                        {detail.assertions_passed.length > 0 && (
                          <div className="space-y-1">
                            <p className="text-xs font-medium text-green-600">PASSED ASSERTIONS</p>
                            <ul className="text-xs space-y-1">
                              {detail.assertions_passed.map((a, i) => (
                                <li key={i} className="flex items-center gap-1">
                                  <CheckCircle className="h-3 w-3 text-green-500" />
                                  {a}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {detail.assertions_failed.length > 0 && (
                          <div className="space-y-1">
                            <p className="text-xs font-medium text-red-600">FAILED ASSERTIONS</p>
                            <ul className="text-xs space-y-1">
                              {detail.assertions_failed.map((a, i) => (
                                <li key={i} className="flex items-center gap-1">
                                  <XCircle className="h-3 w-3 text-red-500" />
                                  {a}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {idx < selectedResult.details.length - 1 && (
                          <hr className="my-4" />
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 text-center text-muted-foreground">
                    <p>Select a test to view details</p>
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
