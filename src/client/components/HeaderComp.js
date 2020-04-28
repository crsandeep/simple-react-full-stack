import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import {
  Navbar, Nav, Form, FormControl, Button
} from 'react-bootstrap';

function prepareLinks(linkMap) {
  const links = [];
  if (linkMap == null) return links;

  if (linkMap.size > 0) {
    for (const [key, value] of linkMap.entries()) {
      links.push(
        <Nav.Link key={key} as={NavLink} to={value}>
          {key}
        </Nav.Link>
      );
    }
  }

  return links;
}

function HeaderComp(props) {
  let links = [];
  if (props.linkMap != null) {
    links = prepareLinks(props.linkMap);
  }

  return (
    // <Navbar bg="light" expand="lg">
    //   <Navbar.Brand as={Link} to='/'>My Space</Navbar.Brand>
    //   <Navbar.Toggle aria-controls="basic-navbar-nav" />
    //   <Navbar.Collapse id="basic-navbar-nav">
    //     <Nav className="mr-auto">
    //       {
    //         links.map(linkComp =>{
    //           return linkComp;
    //         })
    //       }
    //     </Nav>
    //     <Form inline>
    //       <FormControl type="text" placeholder="Search" className="mr-sm-2" />
    //       <Button variant="outline-success">Search</Button>
    //     </Form>
    //   </Navbar.Collapse>
    // </Navbar>
    <nav>
      <Navbar bg="dark" variant="dark">
        <Navbar.Brand href="#home">My Space Master</Navbar.Brand>
        <Nav className="mr-auto">
          <Nav.Link as={NavLink} to="/" exact>Home</Nav.Link>
          <Nav.Link as={NavLink} to="/space">Space</Nav.Link>
          <Nav.Link as={NavLink} to="/grid">Grid</Nav.Link>
          <Nav.Link as={NavLink} to="/item">Item</Nav.Link>
        </Nav>
        <Form inline>
          <FormControl type="text" placeholder="Search Item" className="mr-sm-2" />
          <Button variant="outline-light">Search</Button>
        </Form>
      </Navbar>

    </nav>
  );
}
export default HeaderComp;
