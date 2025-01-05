const express = require("express");
const User = require("../models/User");
const jwt = require("jsonwebtoken");
const router = express.Router();
const OTP = require("../models/OTP");
const sendOTP = require("../utils/sendOTP")


// Register a new user
router.post("/register", async (req, res) => {
  const { email, password, role } = req.body;

  try {
    const existingUser = await User.findOne({ email });
    if (existingUser) return res.status(400).json({ message: "User already exists" });

    const user = new User({ email, password, role });
    await user.save();

    res.status(201).json({ message: "User registered successfully" });
  } catch (error) {
    res.status(500).json({ message: "Error registering user", error });
  }
});

// Login user
router.post("/login", async (req, res) => {
  const { email, password } = req.body;

  try {
    const user = await User.findOne({ email });
    if (!user) return res.status(404).json({ message: "User not found" });

    const isMatch = await user.comparePassword(password);
    if (!isMatch) return res.status(400).json({ message: "Invalid credentials" });

    // Create JWT
    const token = jwt.sign(
      { id: user._id, role: user.role },
      process.env.JWT_SECRET,
      { expiresIn: "1d" }
    );

    res.json({ token, user: { id: user._id, email: user.email, role: user.role } });
  } catch (error) {
    res.status(500).json({ message: "Error logging in", error });
  }
});

// Middleware for verifying token
const verifyToken = (roles = []) => {
  return (req, res, next) => {
    const token = req.header("Authorization");
    if (!token) return res.status(401).json({ message: "Access denied, no token provided" });

    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      req.user = decoded;

      if (roles.length && !roles.includes(decoded.role)) {
        return res.status(403).json({ message: "Access denied, insufficient permissions" });
      }

      next();
    } catch (err) {
      res.status(400).json({ message: "Invalid token" });
    }
  };
};

// Example route for specific roles
router.get("/admin-only", verifyToken(["admin"]), (req, res) => {
  res.send("This is an admin-only route");
});

router.post("/send-otp", async (req, res) => {
  const { email } = req.body;

  try {
    await sendOTP(email);
    res.status(200).json({ message: "OTP sent successfully" });
  } catch (err) {
    res.status(500).json({ error: "Failed to send OTP" });
  }
});

router.post("/verify-otp", async (req, res) => {
  const { email, otp, password } = req.body;

  try {
    const record = await OTP.findOne({ email });

    if (!record || record.otp !== otp || record.expiresAt < new Date()) {
      return res.status(400).json({ error: "Invalid or expired OTP" });
    }

    // OTP verified, register the user
    const user = new User({ email, password });
    await user.save();

    // Remove OTP after successful registration
    await OTP.deleteOne({ email });

    res.status(201).json({ message: "User registered successfully" });
  } catch (err) {
    res.status(500).json({ error: "Failed to register user" });
  }
});

module.exports = router;