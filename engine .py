import math

class MatchEngine:
    def __init__(self, target=None, max_overs=5):
        self.target = target
        self.max_overs = max_overs
        self.max_balls = max_overs * 6
        self.runs = 0
        self.wickets = 0
        self.balls = 0
        self.history = []  # List of tuples: (ball_num, runs, wickets)

    def delivery(self, batter_input: int, bowler_input: int) -> dict:
        """Processes a single ball instance in hand cricket."""
        self.balls += 1
        event = "dot"
        runs_scored = 0
        is_out = False

        if batter_input == bowler_input:
            self.wickets += 1
            is_out = True
            event = "wicket"
        else:
            runs_scored = batter_input
            self.runs += runs_scored
            event = "runs"

        self.history.append((self.balls, self.runs, self.wickets))
        
        return {
            "event": event,
            "runs_scored": runs_scored,
            "total_runs": self.runs,
            "total_wickets": self.wickets,
            "balls": self.balls,
            "overs": f"{self.balls // 6}.{self.balls % 6}"
        }

    def calculate_win_probability(self, current_innings=2) -> dict:
        """
        Calculates mathematical win probability based on remaining criteria.
        Returns a dictionary with percentages for Batting and Bowling sides.
        """
        if self.target is None or current_innings == 1:
            return {"batting_win_pct": 50, "bowling_win_pct": 50}
            
        runs_needed = self.target - self.runs
        balls_left = self.max_balls - self.balls
        wickets_left = 10 - self.wickets # Assuming standard 10 wickets max for team

        if runs_needed <= 0:
            return {"batting_win_pct": 100, "bowling_win_pct": 0}
        if balls_left <= 0 or wickets_left <= 0:
            return {"batting_win_pct": 0, "bowling_win_pct": 100}

        # Mathematical weighting formula for hand cricket probability estimation
        # Base probability calculation using resource ratios
        run_factor = runs_needed / balls_left
        wicket_factor = wickets_left / 10
        
        # Sigmoid scale modeling
        base_score = (wicket_factor * 2.5) - run_factor
        batting_prob = 1 / (1 + math.exp(-base_score))
        
        batting_pct = int(max(5, min(95, batting_prob * 100)))
        bowling_pct = 100 - batting_pct

        return {"batting_win_pct": batting_pct, "bowling_win_pct": bowling_pct}

    def generate_text_graph(self) -> str:
        """Generates a text-based ASCII visual representation of run progression."""
        if not self.history:
            return "No match details data available yet."
            
        graph_lines = ["📈 **MATCH PROGRESSION GRAPH**\n"]
        # Step intervals for plotting 5 data rows
        max_current_runs = max([h[1] for h in self.history]) if self.history else 10
        step = max(1, max_current_runs // 4)
        
        for y in range(max_current_runs, -1, -step):
            line = f"{y:3d} 🏏 |"
            for b in range(1, self.balls + 1):
                # Find matching history node
                node = next((h for h in self.history if h[0] == b), None)
                if node and node[1] >= y and (node[1] - y) < step:
                    line += "🔸" if node[2] > (self.history[self.history.index(node)-1][2] if self.history.index(node)>0 else 0) else "🔹"
                else:
                    line += "  "
            graph_lines.append(line)
            
        graph_lines.append("      " + "—" * (self.balls * 2))
        graph_lines.append("       Balls delivered ➔")
        return "\n".join(graph_lines)
        